+++
title = "Practical BM25"
date = 2026-06-27T00:00:00+08:00
translationKey = "bm25"
tags = ["Sparse Vector"]
categories = ["Tech"]

[params]
toc = true

+++

### References

[Practical BM25 - Part 1: How Shards Affect Relevance Scoring in Elasticsearch | Elastic Blog](https://www.elastic.co/blog/practical-bm25-part-1-how-shards-affect-relevance-scoring-in-elasticsearch)

[Practical BM25 - Part 2: The BM25 Algorithm and its Variables | Elastic Blog](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)

[Practical BM25 - Part 3: Considerations for Picking b and k1 in Elasticsearch | Elastic Blog](https://www.elastic.co/blog/practical-bm25-part-3-considerations-for-picking-b-and-k1-in-elasticsearch)

[tf-idf - Wikipedia](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)

## Background

In Elasticsearch 5.0, the default similarity algorithm was changed to Okapi BM25, which is used to score the relevance between search results and a query. This post focuses on the practical side of BM25, including its available parameters and the factors that affect scoring.

### Understanding How Shards Affect Scoring

Before learning BM25, it is necessary to understand that an Elasticsearch index can be split into multiple shards, which are physical partitions of the index. This matters because BM25 relevance scores are not naturally calculated from global statistics across the entire index. By default, they may be calculated separately inside each shard. The more shards there are, and the less data each shard contains, the easier it is for scoring bias to appear.

Below, we follow the example from the reference article. The goal is to create an Elasticsearch index named `people`, insert a few test documents, and repeatedly search for the same query term `"Shane"` to observe how BM25 relevance scores change with document count and shard distribution.

The author creates an index named `people`, sets it to have 5 primary shards, and uses BM25 as the default similarity algorithm:

```json
PUT people
{
  "settings": {
    "number_of_shards": 5,
    "index" : {
        "similarity" : {
          "default" : {
            "type" : "BM25"
          }
        }
    }
  }
}
```

The author uses his own name as the example:

```json
PUT /people/_doc/1
{
  "title": "Shane"
}
GET /people/_doc/_search
{
    "query": {
        "match": {
             "title": "Shane"
         }
      }
}
```

The search looks for documents whose `title` field matches `"Shane"`, so it naturally matches `/people/_doc/1`:

```json
PUT /people/_doc/2
{
  "title": "Shane C"
}
PUT /people/_doc/3
{
  "title": "Shane Connelly"
}
PUT /people/_doc/4
{
  "title": "Shane P Connelly"
}
```

Then the same search is run again:

```json
GET /people/_doc/_search
{
    "query": {
        "match": {
             "title": "Shane"
         }
      }
}
```

At this point there are 4 "documents":

1. Shane
2. Shane C
3. Shane Connelly
4. Shane P Connelly

The search finds documents whose `title` field matches `"Shane"`. Although all titles contain `"Shane"`, their BM25 scores are not the same. The result is that `doc1` and `doc3` both score 0.2876821, while `doc2` scores 0.19856805 and `doc4` scores 0.16853254.

Although `doc2` and `doc3` look similar, their scores differ a lot. This is not mainly caused by the difference between `"C"` and `"Connelly"`, but by how documents are distributed across shards. So how can the scores become more consistent?

1. The larger the dataset, the smaller the statistical difference between shards.

2. Reducing the number of shards can reduce scoring bias.

3. If you want BM25 scores under multiple shards to be closer to "global statistics", you can add `?search_type=dfs_query_then_fetch` when querying. It collects term-frequency statistics from all shards first, then calculates scores in a unified way, so the result will be close to, or even the same as, the result when `number_of_shards=1`.

   > `dfs_query_then_fetch` first aggregates term-frequency statistics across shards and then calculates BM25 scores, making multi-shard scoring closer to single-shard global scoring. However, it adds one extra communication round, so it is only worth using when the dataset is small, there are many shards, the data distribution is uneven, and relevance scores matter a lot.

## Algorithm and its variables

BM25 model:

$$
\sum_{i}^{n} IDF(q_i) \frac{f(q_i, D) * (k_1 + 1)}{f(q_i, D) + k_1 * (1 - b + b * \frac{fieldLen}{avgFieldLen})}
$$

- $q_i$: the $i$-th keyword in the query.
- $IDF(q_i)$: the inverse document frequency of keyword $q_i$.
- $f(q_i, D)$: the term frequency of keyword $q_i$ in document $D$.
- **$fieldLen$**: the length of the current document field.
- $avgFieldLen$: the average field length across all documents in the index.
- $k_1$ and $b$: tunable parameters. Usually $k1 \in [1.2, 2.0]$, and $b = 0.75$.

In simple terms, BM25 is a TF-IDF model that introduces nonlinearity and handles the frequency saturation problem. The TF-IDF model is:

$$
\text{Score} = f(q_i, D) \times \log\left(\frac{N}{n(q_i)}\right)
$$

#### $q_i$

For example, if I search for "shane", there is only one query term, so $q_0$ is "shane". If I search for "shane connelly" in English, Elasticsearch recognizes the space and tokenizes the query into two terms: $q_0$ is "shane", and $q_1$ is "connelly". These query terms are substituted into the other parts of the formula, and the final results are summed.

#### $IDF(q_i)$

The **IDF (Inverse Document Frequency)** part of the formula measures how frequently a term appears across all documents. It "penalizes" common terms by lowering their weight. In the Lucene/BM25 algorithm, the actual formula is:

$$
\ln \left( 1 + \frac{(docCount - f(q_i) + 0.5)}{f(q_i) + 0.5} \right)
$$

Here, $docCount$ is the total number of documents in this shard that contain a value for this field. If the `search_type=dfs_query_then_fetch` parameter is used, it is the count across all shards. $f(q_i)$ is the number of documents containing the $i$-th query term. In the example, the term "shane" appears in all 4 documents, so the inverse document frequency $IDF(\text{"shane"})$ is:

$$
\ln\left(1 + \frac{(4 - 4 + 0.5)}{4 + 0.5}\right) = \ln\left(1 + \frac{0.5}{4.5}\right) = 0.105360515657826
$$

$IDF(\text{"connelly"})$ is:

$$
\ln\left(1 + \frac{(4 - 2 + 0.5)}{2 + 0.5}\right) = \ln\left(1 + \frac{2.5}{2.5}\right) = 0.693147180559945
$$

We can see that queries containing rarer terms have a higher multiplier. In this 4-document corpus, "connelly" is rarer than "shane", so it contributes more to the final score. This matches intuition: the word "the" may appear in almost every English document, so when a user searches for something like "the elephant", "elephant" is clearly more important than "the", and we also expect it to contribute more to the search score.

#### $fieldLen/avgFieldLen$

The more terms a document contains, at least terms that do not match the query, the lower the document score tends to be. This also matches intuition: if a 300-page document mentions my name only once, it is probably less relevant than a short tweet that also mentions my name once.

#### $b$

The larger the value of $b$, the more the document length ratio affects the score. To understand this, imagine setting $b$ to 0. In that case, the length ratio has no effect at all, and the score is only affected by term frequency. Document length does not affect scoring. If $b$ is set to 1, the score is affected only by the length ratio and not by frequency.

#### $f(q_i, D)$

This value corresponds to TF, or Term Frequency.

$f(q_i, D)$ means: how many times does the $i$-th query term appear in document $D$? In all of the example documents, $f(\text{"shane"}, D)$ is 1, but $f(\text{"connelly"}, D)$ differs: it is 1 in documents 3 and 4, and 0 in documents 1 and 2. If there were a 5th document whose text was "shane shane", then $f(\text{"shane"}, D)$ would be 2. We can see that $f(q_i, D)$ appears in both the numerator and denominator, together with a special factor called "$k_1$", which is discussed below. The basic intuition is that the more often a query term appears in a document, the higher the score becomes. A document that mentions our name multiple times is more likely to be relevant than one that mentions it only once.

#### $k_1$

In BM25, $k_1$ is the core parameter controlling term frequency saturation. It sets an asymptotic upper bound for the contribution of $f(q_i, D)$ to the relevance score, making the marginal gain decrease nonlinearly as term frequency increases. Compared with the almost linear weight growth in traditional TF-IDF, this mechanism effectively suppresses excessive ranking influence from high-frequency terms, such as keyword stuffing. The value of $k_1$ directly determines how quickly the score approaches saturation: a smaller $k_1$ makes term frequency contribution hit the bottleneck quickly, while a larger $k_1$ allows term frequency to maintain meaningful weight gains over a wider range.

If $k_1$ is set to 0, the score becomes fixed at 1. If $k_1$ is set to a very large value, such as 10000, the formula approximately degenerates into $\frac{TF \times k_1}{k_1} = TF$, becoming term frequency itself.

## Picking $b$ and $k_1$

Regarding the values of $b$ and $k_1$, the Elasticsearch article also points out that the current defaults are empirical values that work for most cases, but **there is no globally optimal b and k1. They must be evaluated together with the corpus and queries.**

Also, when retrieval performance is not good enough, the following should be optimized before tuning $b$ and $k_1$:

1. Boost exact phrase matches.
2. Use synonyms to expand expressions that users may care about.
3. Use analysis components such as fuzziness, typeahead, phonetic matching, and stemming to handle spelling mistakes, language differences, and word-form variations.
4. Use function score to adjust document scores based on publish time, geographical distance, or business features.

As for the Explain API in the later part of the Elasticsearch article, I will not expand on it here.
