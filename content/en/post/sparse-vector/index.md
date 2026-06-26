+++
title = "Sparse Vectors and the SPLADE Model"
date = 2026-06-27T00:00:00+08:00
translationKey = "splade-hybrid-search"
tags = ["Sparse Vector", "SPLADE", "RAG"]
categories = ["Tech"]

[params]
toc = true

+++

## References

- [Naver SPLADE official repository](https://github.com/naver/splade)
- [naver/splade_v2_max model page](https://huggingface.co/naver/splade_v2_max)
- [Sentence Transformers Sparse Encoder documentation](https://www.sbert.net/docs/package_reference/sparse_encoder/index.html)
- [Sentence Transformers Sparse Encoder training overview](https://www.sbert.net/docs/sparse_encoder/training_overview.html)
- [Sentence Transformers Sparse Encoder inference efficiency](https://sbert.net/docs/sparse_encoder/usage/efficiency.html)

# Sparse Vectors and the SPLADE Model

In RAG systems, dense vectors have become the most common retrieval method. They map text into a continuous vector space and are good at capturing semantically similar expressions, such as "employee resignation process" and "personnel exit procedure". However, dense vectors also have clear weaknesses: they are not always good at exact matching for entities, IDs, terminology, error codes, product models, table field names, and code snippets.

This is where sparse vectors become valuable. They are more like a neural-network-enhanced inverted index: text is still represented as sparse weights over term dimensions, but these weights are not calculated by pure statistical methods like BM25. Instead, they are predicted by a model.

In short:

- Dense vectors handle semantic similarity.
- BM25 handles exact lexical matching.
- SPLADE sparse vectors handle weighted matching after neural term expansion.
- Hybrid Search merges dense and sparse retrieval results.

## Paper model

SPLADE maps a piece of text into vocabulary space based on the logits of a Masked Language Model. Suppose the vocabulary contains 30522 WordPiece tokens. Each text can eventually be represented as:

```text
token_id -> weight
```

This is a sparse vector. Most token weights are 0, and only a small number of tokens that the model considers important have non-zero weights.

The biggest difference from ordinary embeddings is that each dimension in a dense embedding is usually not interpretable, while each dimension in a sparse vector is a vocabulary token. A token activated by the model can be understood as "this text is related to this term".

For example, a document may not explicitly contain the word "reimbursement", but it may contain "travel expense", "invoice", and "approval form". SPLADE may activate tokens related to "reimbursement". Then, when the query is "reimbursement process", the document may still be retrieved even if it does not exactly match the original term.

More specifically, SPLADE uses the logits from the Masked Language Model layer to predict the importance of each term in the BERT WordPiece vocabulary. Suppose the tokenized input text is:

$$
t=(t_{1},t_{2},...,t_{N})
$$

and the corresponding contextual representations are:

$$
(h_{1},h_{2},...,h_{N})
$$

For the $i$-th token in the input, the model calculates its importance for the $j$-th token in the vocabulary:

$$
w_{ij}=transform(h_{i})^{T}E_{j}+b_{j}, \quad j\in\{1,...,|V|\}
$$

Here, $E_j$ is the BERT input embedding of vocabulary ${token}_j$, and $b_j$ is the token-level bias. `transform(.)` is usually a linear transformation with GeLU and LayerNorm. Intuitively, this step asks: for this position in the input, how related is it to each term in the vocabulary?

However, retrieval does not need "the score of a term at one position". It needs "the score of a term for the whole text". Therefore, SPLADE aggregates activations from different positions into a sparse representation for the whole text:

$$
w_{j}=\sum_{i\in t}\log(1+ReLU(w_{ij}))
$$

There are three meanings in this formula:

- `ReLU` sets negative scores to zero and keeps only positively related terms.
- $log(1+x)$ performs logarithmic saturation, preventing scores of frequent or repeated words from growing without bound.
- $\sum$ accumulates activations from different positions for the same vocabulary token, producing the term weight for the whole text.

Finally, the text becomes a high-dimensional but sparse vector:

```text
token_id -> weight
```

After both the query and document are mapped into the same vocabulary space, the retrieval score is the dot product of sparse vectors:

$$
s(q,d)=\sum_j w_j^q w_j^d
$$

This is also why SPLADE can be connected to inverted indexes or sparse vector indexes.

### Ranking loss

During training, SPLADE needs to make relevant documents score higher and irrelevant documents score lower. Given a query $q_i$, a positive document $d_i^+$, a hard negative document $d_i^-$, and a group of in-batch negative documents ${d_{i,j}^{-}}$, a contrastive ranking loss similar to the following can be used:

$$
\mathcal{L}_{rank-IBN} =
-\log
\frac{e^{s(q_i,d_i^+)}}
{e^{s(q_i,d_i^+)} + e^{s(q_i,d_i^-)} + \sum e^{s(q_i,d_{i,j}^{-})}}
$$

Its goal is direct: make the probability of the positive document as large as possible within the candidate set. From an engineering perspective, the model keeps learning which term expansions help it rank the correct document higher.

### FLOPS sparsity regularization

If only ranking quality is optimized, the model may activate too many tokens. This may improve recall, but the inverted index becomes larger, and queries need to access more posting lists.

Therefore, SPLADE introduces FLOPS regularization to control sparsity. For a batch of documents, first estimate the average activation of vocabulary token \(j\) in this batch:

$$
\overline{a}_{j}=\frac{1}{N}\sum_{i=1}^{N}w_{j}^{(d_i)}
$$

Then square and sum the average activations:

$$
l_{FLOPS}=\sum_{j\in V}\overline{a}_{j}^{2}
=\sum_{j\in V}(\frac{1}{N}\sum_{i=1}^{N}w_{j}^{(d_i)})^{2}
$$

This regularization term is not simply controlling "vector dimensionality". It controls the number and distribution of non-zero tokens. It tries to prevent the model from binding many documents to a few high-frequency words, and also prevents every document from activating too many terms.

Therefore, the sparsity weight can be understood as a knob between recall quality and retrieval cost:

- Larger weight: shorter sparse vectors, smaller index, faster retrieval, but possibly lower recall.
- Smaller weight: longer sparse vectors and richer expansion, but higher index and retrieval cost.

### Overall loss

Finally, SPLADE trains ranking loss and sparsity regularization together:

$$
\mathcal{L}=\mathcal{L}_{rank-IBN}
+\lambda_q\mathcal{L}_{reg}^{q}
+\lambda_d\mathcal{L}_{reg}^{d}
$$

Here, \(\lambda_q\) controls query-side sparsity, and \(\lambda_d\) controls document-side sparsity. Query-side sparsity is usually very important because queries are more sensitive to latency. Document-side vectors can be computed offline, so slightly higher compute cost is often acceptable, but index size still needs to be controlled.

### From sum pooling to max pooling

The original SPLADE aggregates term predictions from every input position:

$$
w_{j}=\sum_{i\in t}\log(1+ReLU(w_{ij}))
$$

The more common later SPLADE-max uses max pooling:

$$
w_{j}=\max_{i\in t}\log(1+ReLU(w_{ij}))
$$

This does not mean the whole text only keeps one token. Instead, it takes the maximum activation separately for each vocabulary dimension. This can reduce amplification from long text or repeated words, making the representation focus more on whether a semantic term is strongly activated, rather than simply depending on occurrence count.

### SPLADE-doc and distillation training

Standard SPLADE encodes both query and document. In other words, both query-side and document-side representations may produce neural expansion terms. Retrieval calculates:

$$
s(q,d)=\sum_j w_j^q w_j^d
$$

SPLADE-doc is more focused on engineering efficiency. It only applies SPLADE encoding on the document side, while the query side usually uses only the original query tokens. The document score can be written as:

$$
s(q,d)=\sum_{j\in q}w_j^d
$$

This means document-side expansion can be precomputed offline, and the query side does not need to run a SPLADE encoder, reducing latency. The tradeoff is that the query side has no neural expansion ability and can only use "document-side expansion".

In addition, many strong SPLADE models use knowledge distillation and hard negatives. A common approach is to first train a first-stage retriever and a cross-encoder reranker, then continue training with harder negatives and reranker scores. In engineering practice, we do not have to reproduce this whole training pipeline to use public models. But understanding it helps explain why words like `distil`, `ensemble`, and `cocondenser` appear in model names.

### Why sparsity matters

If the model activates many tokens, recall may improve, but the index becomes larger and retrieval becomes slower. SPLADE uses FLOPS regularization to control the number and distribution of non-zero tokens.

From an engineering perspective, sparse vectors are not better just because they are longer.

- Too few non-zero tokens: the index is small and retrieval is fast, but recall may be insufficient.
- Too many non-zero tokens: recall may be better, but the index expands and retrieval cost increases.

In practice, secondary pruning is often applied, such as:

- Keeping only the top_k tokens.
- Filtering tokens whose weight is below a threshold.
- Limiting the maximum number of sparse dimensions for a single chunk.

These parameters often affect online cost more than the model itself.

## Model selection

SPLADE is more like a family of sparse neural retrieval methods than a single model. The official Naver repository also notes that different regularization strengths produce models ranging from "very sparse" to "strong query/doc expansion". Their effectiveness, index size, and latency all differ.

If the goal is only to quickly validate engineering feasibility, `naver/splade-cocondenser-ensembledistil` is a good starting point. It is a common strong model in the official SPLADE++ series. The Naver repository reports its MS MARCO dev MRR@10 as 38.3, higher than `splade_v2_max` at 34.0 and `splade_v2_distil` at 36.8. It is suitable for first checking whether sparse retrieval can fill the keyword, entity, and terminology recall gaps of dense retrieval.

If inference cost matters more, consider `naver/splade_v2_max` or the efficient SPLADE series. `splade_v2_max` is structurally simple. Its Hugging Face model page marks it as DistilBERT base, with a 512-token maximum length, 30522-dimensional output, and dot-product similarity. The efficient SPLADE series further separates document encoder and query encoder, aiming to reduce query-side latency.

A practical selection order is:

- First choose a strong public model for offline evaluation, such as `naver/splade-cocondenser-ensembledistil`.
- If offline evaluation is effective, then measure average non-zero token count, index size, document-side encoding throughput, and query-side P95 latency.
- If query-side latency is too high, first try query caching, ONNX/OpenVINO, quantization, or efficient SPLADE.
- If the index is too large, first reduce top-k, increase the minimum weight threshold, or choose a model with stronger regularization and higher sparsity.
- If business data differs greatly from public English retrieval datasets, consider fine-tuning with domain data instead of directly trusting public leaderboards.

Do not choose a model only by MRR. SPLADE model selection should consider at least five things at the same time: retrieval quality, average non-zero dimensions, index size, query latency, and deployment complexity.

Sentence Transformers now provides `SparseEncoder`, which can directly load SPLADE models:

```python
from sentence_transformers import SparseEncoder

model = SparseEncoder("naver/splade-cocondenser-ensembledistil")
embeddings = model.encode(["example query"])
```

It also provides `encode_query()`, `encode_document()`, sparsity statistics, Qdrant/Elasticsearch/OpenSearch integration, and deployment capabilities related to ONNX/OpenVINO/quantization. For engineering prototypes, this route can be used first, and then the implementation can be moved to a custom inference service depending on performance bottlenecks.

## Differences between SPLADE and BM25

BM25 and SPLADE can both use inverted indexes for retrieval, but their weights come from different sources.

BM25 weights come from statistics, such as TF, IDF, and document length normalization. It mainly depends on exact matching between query terms and document terms.

SPLADE weights come from neural model predictions. It can not only preserve tokens that appear in the original text, but may also activate semantically related tokens that do not appear in the original text.

So it can be roughly understood as:

```text
BM25   = statistical matching of original terms
SPLADE = weighted matching of neural expansion terms
```

In enterprise knowledge bases, technical documentation, customer-service FAQs, code documentation, policies, and regulations, both BM25 and SPLADE are valuable. BM25 is lighter, while SPLADE is stronger but more expensive.
