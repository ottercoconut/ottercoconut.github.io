+++

title = "稀疏向量：从SPLADE模型到工程落地"
date = 2026-05-12T16:17:17+08:00
translationKey = "splade-hybrid-search"
tags = ["稀疏向量", "SPLADE", "RAG"]
categories = ["技术"]

[params]
toc = true

+++

## 参考网站

- [Naver SPLADE 官方仓库](https://github.com/naver/splade)
- [naver/splade_v2_max 模型页](https://huggingface.co/naver/splade_v2_max)
- [Sentence Transformers Sparse Encoder 文档](https://www.sbert.net/docs/package_reference/sparse_encoder/index.html)
- [Sentence Transformers Sparse Encoder 训练概览](https://www.sbert.net/docs/sparse_encoder/training_overview.html)
- [Sentence Transformers Sparse Encoder 推理加速](https://sbert.net/docs/sparse_encoder/usage/efficiency.html)

# 稀疏向量：从SPLADE模型到工程落地

在 RAG 系统里，dense vector 已经是最常见的召回方式。它把文本映射到连续向量空间中，适合捕捉语义相近的表达，例如“员工离职流程”和“人员退出手续”。但 dense vector 也有明显短板：它不一定擅长精确匹配实体、编号、术语、错误码、产品型号、表格字段名和代码片段。

这时 sparse vector 就有价值了。它更像一个“神经网络增强版倒排索引”：文本仍然被表示为词项维度上的稀疏权重，但这些权重不是 BM25 这类纯统计方法算出来的，而是由模型预测出来的。

简单说：

- dense vector 负责语义相似。
- BM25 负责原词匹配。
- SPLADE sparse vector 负责神经词项扩展后的加权匹配。
- Hybrid Search 则把 dense 和 sparse 两种召回结果融合起来。

## 论文模型

SPLADE 基于 Masked Language Model 的 logits，把一段文本映射到词表空间中。假设词表里有 30522 个 WordPiece token，那么每个文本最终可以表示为：

```text
token_id -> weight
```

也就是一个稀疏向量。大部分 token 的权重为 0，只有少量被模型认为重要的 token 会有非零权重。

这和普通 embedding 最大的区别是：dense embedding 的每一维通常不可解释，而 sparse vector 的维度就是词表 token。一个被模型激活的 token 可以理解为“这段文本与这个词项相关”。

例如一段文档没有显式出现“报销”，但出现了“差旅费”“发票”“审批单”，SPLADE 可能会激活与“报销”相关的 token。这样在查询“报销流程”时，即便文档没有完全命中原词，也可能被召回。

更具体地说，SPLADE 会利用 Masked Language Model 层的 logits，在 BERT WordPiece 词表中预测每个词项的重要性。假设输入文本在分词后是：

$$
t=(t_{1},t_{2},...,t_{N})
$$

对应的上下文表示是：

$$
(h_{1},h_{2},...,h_{N})
$$

那么对输入中第 $i$ 个 token，模型会计算它对词表中第 $j$ 个 token 的重要性：

$$
w_{ij}=transform(h_{i})^{T}E_{j}+b_{j}, \quad j\in\{1,...,|V|\}
$$

这里 $E_j$ 词表 ${token}_j$ 的 BERT 输入嵌入，$b_j$ 是 token 级偏置，`transform(.)` 通常是带 GeLU 和 LayerNorm 的线性变换。直觉上，这一步是在问：输入里的这个位置，和词表里的每个词项分别有多相关。

但检索时需要的不是“某个位置对某个词的分数”，而是“整段文本对某个词的分数”。因此 SPLADE 会把不同位置的激活聚合成整段文本的稀疏表示：

$$
w_{j}=\sum_{i\in t}\log(1+ReLU(w_{ij}))
$$

这个公式里有三层含义：

- `ReLU` 把负分清零，只保留正向相关的词项。
- $log(1+x)$ 做对数饱和，避免高频词或重复词的分数被无限放大。
- $\sum$ 把不同位置对同一个词表 token 的激活累加起来，得到整段文本的词项权重。

最后，文本就变成了一个很高维但很稀疏的向量：

```text
token_id -> weight
```

查询和文档都映射到同一个词表空间后，检索分数就是稀疏向量点积：

$$
s(q,d)=\sum_j w_j^q w_j^d
$$

这也是 SPLADE 能接入倒排索引或稀疏向量索引的原因。

### 排序损失

训练时，SPLADE 要让相关文档得分更高，不相关文档得分更低。给定一个查询 $q_i$ 、一个正样本文档 $d_i^+$ 、一个困难负样本 $d_i^-$ ，以及一组批内负样本 ${d_{i,j}^{-}}$ ，可以使用类似下面的对比排序损失：

$$
\mathcal{L}_{rank-IBN} =
-\log
\frac{e^{s(q_i,d_i^+)}}
{e^{s(q_i,d_i^+)} + e^{s(q_i,d_i^-)} + \sum e^{s(q_i,d_{i,j}^{-})}}
$$

它的目标很直接：让正样本在候选集合里的概率尽可能大。工程上可以理解为，模型会不断学习哪些词项扩展能帮助它把正确文档排到前面。

### FLOPS 稀疏正则

如果只优化排序效果，模型可能会激活太多 token。这样虽然召回可能变强，但倒排索引会膨胀，查询时需要访问的 posting list 也会变多。

因此 SPLADE 引入 FLOPS 正则来控制稀疏性。对一批文档来说，可以先估计词表 token \(j\) 在这批文档中的平均激活：

$$
\overline{a}_{j}=\frac{1}{N}\sum_{i=1}^{N}w_{j}^{(d_i)}
$$

然后对平均激活做平方求和：

$$
l_{FLOPS}=\sum_{j\in V}\overline{a}_{j}^{2}
=\sum_{j\in V}(\frac{1}{N}\sum_{i=1}^{N}w_{j}^{(d_i)})^{2}
$$

这个正则项不是简单控制“向量维度”，而是在控制非零 token 的数量和分布。它希望模型不要把大量文档都绑定到少数高频词上，也不要让每个文档都激活过多词项。

因此，稀疏性权重可以理解为一个召回质量和检索成本之间的旋钮：

- 权重更大：稀疏向量更短，索引更小，检索更快，但可能损失召回。
- 权重更小：稀疏向量更长，扩展更丰富，但索引和检索成本更高。

### 总体损失

最终，SPLADE 会把排序损失和稀疏正则放在一起训练：

$$
\mathcal{L}=\mathcal{L}_{rank-IBN}
+\lambda_q\mathcal{L}_{reg}^{q}
+\lambda_d\mathcal{L}_{reg}^{d}
$$

其中 \(\lambda_q\) 控制查询侧稀疏性，\(\lambda_d\) 控制文档侧稀疏性。查询侧通常对延迟更敏感，所以查询侧稀疏性非常重要。文档侧可以离线计算，通常可以接受更高一点的计算成本，但仍然要控制索引体积。

### 从求和到最大池化

原始 SPLADE 会对输入文本中每个位置的词项预测进行聚合：

$$
w_{j}=\sum_{i\in t}\log(1+ReLU(w_{ij}))
$$
后续更常见的 SPLADE-max 使用最大池化：

$$
w_{j}=\max_{i\in t}\log(1+ReLU(w_{ij}))
$$
这并不是整段文本只保留一个 token，而是对词表里的每个维度分别取最大激活值。这样可以减少长文本或重复词带来的累加放大，让表示更关注“是否强烈激活某个语义词项”，而不是简单依赖出现次数。

### SPLADE-doc 与蒸馏训练

标准 SPLADE 会同时编码 query 和 document。也就是说，查询侧和文档侧都可能产生神经扩展词项，检索时计算的是：

$$
s(q,d)=\sum_j w_j^q w_j^d
$$

SPLADE-doc 则更偏工程效率。它只在文档侧做 SPLADE 编码，查询侧通常只使用原始 query token，文档得分可以写成：

$$
s(q,d)=\sum_{j\in q}w_j^d
$$

这样文档侧扩展可以离线预计算，查询侧不需要跑 SPLADE encoder，延迟会更低。代价是 query 侧没有神经扩展能力，只能利用“文档侧扩展”。

另外，很多效果较强的 SPLADE 模型会使用知识蒸馏和困难负样本。常见做法是先训练一个第一阶段检索器和 cross-encoder 重排器，再用更难的负样本和重排器分数继续训练。工程上不用自己复现这套训练流程，也能使用公开模型；但理解这一点有助于判断模型名称里 `distil`、`ensemble`、`cocondenser` 这类词为什么会出现。

### 稀疏性为什么重要

如果模型把大量 token 都激活，召回效果也许会上升，但索引会变大，检索会变慢。SPLADE 使用 FLOPS 正则化来控制非零 token 的数量和分布。

工程上可以把它理解为：稀疏向量不是越长越好。

- 非零 token 太少：索引小、检索快，但召回可能不够。
- 非零 token 太多：召回可能更好，但索引膨胀，检索成本上升。

落地时通常还会做二次裁剪，例如：

- 只保留 top_k 个 token
- 过滤 weight 低于阈值的 token
- 限制单个 chunk 的最大稀疏维度数量

这些参数往往比模型本身更影响线上成本。

## 模型选择

SPLADE 更像一类稀疏神经检索方法，而不是单一模型。Naver 官方仓库也特别提醒：不同正则化强度会得到从“非常稀疏”到“强 query/doc 扩展”的不同模型，效果、索引大小和延迟都会变。

如果只是想快速做工程验证，可以从 `naver/splade-cocondenser-ensembledistil` 开始。它是官方 SPLADE++ 系列里常见的强效果模型，在 Naver 官方仓库列出的 MS MARCO dev MRR@10 为 38.3，高于 `splade_v2_max` 的 34.0 和 `splade_v2_distil` 的 36.8。它适合先验证 sparse 召回是否能补足 dense 的关键词、实体、术语召回缺口。

如果更看重推理成本，可以看 `naver/splade_v2_max` 或 efficient SPLADE 系列。`splade_v2_max` 结构简单，Hugging Face 模型页标注为 DistilBERT base、512 token 最大长度、30522 维输出、点积相似度。efficient SPLADE 系列则进一步区分 document encoder 与 query encoder，目标是降低查询侧延迟。

一个实用的选型顺序是：

- 先选一个效果强的公开模型做离线评测，例如 `naver/splade-cocondenser-ensembledistil`。
- 如果离线评测有效，再统计平均非零 token 数、索引大小、文档侧编码吞吐和查询侧 P95 延迟。
- 如果查询侧太慢，优先尝试 query 缓存、ONNX/OpenVINO、量化或 efficient SPLADE。
- 如果索引太大，优先调小 top-k、提高最小权重阈值，或选择更强正则化、更稀疏的模型。
- 如果业务语料和公开英文检索数据差异很大，再考虑用领域数据微调，而不是直接相信公开榜单。

不要只按 MRR 选模型。SPLADE 选型至少要同时看五件事：检索效果、平均非零维度、索引体积、查询延迟、部署复杂度。

Sentence Transformers 现在提供了 `SparseEncoder`，可以直接加载 SPLADE 模型：

```python
from sentence_transformers import SparseEncoder

model = SparseEncoder("naver/splade-cocondenser-ensembledistil")
embeddings = model.encode(["example query"])
```

它也提供 `encode_query()`、`encode_document()`、稀疏度统计、Qdrant/Elasticsearch/OpenSearch 集成，以及 ONNX/OpenVINO/量化相关部署能力。工程上可以优先用这条路线做原型，再根据性能瓶颈决定是否切到自定义推理服务。

## SPLADE 和 BM25 的区别

BM25 和 SPLADE 都可以使用倒排索引完成检索，但权重来源不同。

BM25 的权重来自统计量，例如 TF、IDF 和文档长度归一化。它主要依赖 query 原词和 document 原词的精确匹配。

SPLADE 的权重来自神经模型预测。它不仅可以保留原文出现的 token，也可能激活原文没有出现但语义相关的 token。

因此可以粗略理解为：

```text
BM25   = 原始词项的统计匹配
SPLADE = 神经扩展词项的加权匹配
```

在企业知识库、技术文档、客服 FAQ、代码文档、规范制度等场景中，BM25 和 SPLADE 都很有价值。BM25 更轻，SPLADE 更强但成本更高。

## 入库链路怎么设计

一个通用的 RAG 入库链路可以设计成：

```text
document
  -> parse
  -> chunk
  -> persist chunk truth
  -> dense embedding
  -> sparse embedding
  -> upsert vector index
  -> mark indexed
```

关键点是：dense vector 和 sparse vector 应该绑定同一个 chunk 主键。

推荐的数据关系是：

```text
chunk_id
  -> chunk text
  -> metadata
  -> dense vector
  -> sparse vector
```

这样检索时无论命中 dense 还是 sparse，都能回到同一个 chunk。融合、去重、重排和上下文组装都会简单很多。

### 同一个 chunk_id 下保存 dense 和 sparse

如果向量数据库支持 named vectors，可以在同一个 point 下保存多种向量：

```python
PointStruct(
    id=chunk_id,
    vector={
        "dense": dense_vector,
        "sparse": SparseVector(
            indices=sparse_indices,
            values=sparse_values,
        ),
    },
    payload={
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "dataset_id": dataset_id,
        "user_id": user_id,
    },
)
```

collection 可以配置为：

```python
vectors_config={
    "dense": VectorParams(
        size=dense_vector_size,
        distance=Distance.COSINE,
    ),
},
sparse_vectors_config={
    "sparse": SparseVectorParams(),
}
```

这种方式的优点是生命周期统一：新增、更新、删除、补偿都围绕一个 point 和一个 `chunk_id` 进行。

### 平行 collection

如果现有系统已经有大量历史 dense vector，并且 collection 结构不方便迁移，可以先采用平行 collection：

```text
dense collection:
  id = chunk_id
  vector = dense

sparse collection:
  id = chunk_id
  vector = sparse
```

这种方式迁移风险低，因为不会破坏原有 dense collection。但检索时需要分别查询两个 collection，再在应用层按 `chunk_id` 融合。

长期看，如果向量数据库支持 hybrid point，同一个 point 下保存 dense + sparse 会更自然。

### 状态机怎么设计

入库链路里，dense 和 sparse 可能独立失败。一个常见问题是：dense 成功、sparse 失败时，文档是否算入库成功？

这取决于产品策略。

如果系统要求 hybrid index 完整后才可检索，可以把 dense 和 sparse 视为同一个整体状态：

```text
PENDING -> INDEXING -> INDEXED
                   -> FAILED
```

只有 dense 和 sparse 都写入成功，才标记 `INDEXED`。

如果系统允许降级检索，则建议拆开状态：

```text
dense_status:  PENDING / SUCCESS / FAILED
sparse_status: PENDING / SUCCESS / FAILED
index_status:  PARTIAL / READY / FAILED
```

这样 sparse 失败时仍然可以提供 dense-only 检索，同时把 sparse 重建交给后台补偿任务。

一般来说，生产系统更推荐第二种。它复杂一点，但可用性更好。

### 写入失败与补偿

向量索引通常是外部系统，不应该被当成强事务的一部分。更合理的做法是：

```text
1. 先落 chunk 真值
2. 再写 dense/sparse 索引
3. 最后回写索引状态
4. 失败时保留可重建依据
```

补偿任务需要覆盖这些场景：

- MySQL 已经是 `INDEXING`，但向量库 point 不存在。
- dense point 存在，sparse vector 缺失。
- sparse 写入成功，但状态回写失败。
- chunk 内容更新后，旧向量没有被覆盖。
- chunk 删除后，向量库残留 point。

只要 chunk 真值、模型名、分片参数还在，dense/sparse 索引都应该可以重建。

## 查询

最简单的融合方式是加权分数：

```text
final_score = alpha * dense_score + beta * sparse_score
```

但 dense 和 sparse 的分数分布经常不一致，直接加权需要做归一化。否则某一路分数可能天然更大，压过另一条召回。

更稳妥的初始方案是 RRF：

```text
rrf_score(d) = sum(1 / (k + rank_i))
```

RRF 只依赖排名，不强依赖原始分数分布，适合早期上线和 A/B 实验。

一个常见流程是：

1. dense top_k = 50
2. sparse top_k = 50
3. RRF 融合得到 top_n = 30
4. cross-encoder rerank
5. 取最终 top_m 组装上下文

如果没有 rerank 阶段，可以适当提高召回数量，再用规则过滤低质量 chunk。

### Hybrid Search

只用 dense vector，容易漏掉精确词项。只用 sparse vector，可能错过语义改写。

Hybrid Search 的基本思路是两条召回并行：

```text
query
  -> dense query embedding
  -> sparse query embedding
  -> dense search
  -> sparse search
  -> merge by document_id / chunk_id
  -> fusion
  -> rerank
```

dense 负责“意思像”，sparse 负责“词项准”。两者融合后，召回通常会更稳。

## 参数建议

初期可以从保守参数开始：

```text
sparse_top_k_per_chunk = 128
sparse_min_weight = 0.0 或 0.01
dense_recall_top_k = 50
sparse_recall_top_k = 50
rrf_k = 60
```

如果索引体积太大，优先降低 `sparse_top_k_per_chunk`。如果召回不够，再逐步增大。

线上需要观察：

- 每个 chunk 平均非零 token 数。
- sparse index 体积。
- sparse 查询延迟。
- dense/sparse 召回重叠率。
- sparse 独有召回的最终命中率。
- hybrid 相比 dense-only 的答案质量提升。

## 常见坑

- `chunk_id` 不统一：dense 和 sparse 如果使用不同 ID，后续融合会非常麻烦。最好从一开始就统一使用同一个 `chunk_id`。
- collection 结构不可直接升级：有些向量数据库从匿名 dense vector 切到 named vectors 需要重建 collection。上线前要规划 migration，而不是直接改写生产 collection 配置。
- sparse token 太多：不做 top-k 或阈值过滤，索引体积可能快速膨胀。稀疏向量不是越长越好。
- 查询侧延迟被忽略：标准 SPLADE 查询也要跑 encoder。如果没有缓存或独立服务，延迟可能明显上升。
- 分数直接相加：dense 和 sparse 原始分数分布不同，直接相加容易偏向某一路召回。早期建议优先用 RRF。
- 缺少补偿任务：向量库写入成功但状态回写失败、状态成功但 point 缺失，这些情况都可能发生。没有补偿任务，索引会逐渐漂移。
