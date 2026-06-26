+++

title = "Practical BM25"
date = 2026-05-09T13:30:00+08:00
translationKey = "bm25l"
tags = ["稀疏向量"]
categories = ["技术"]

[params]
toc = true

+++

### 参考网站

[Practical BM25 - Part 1: How Shards Affect Relevance Scoring in Elasticsearch | Elastic Blog](https://www.elastic.co/blog/practical-bm25-part-1-how-shards-affect-relevance-scoring-in-elasticsearch)

[Practical BM25 - Part 2: The BM25 Algorithm and its Variables | Elastic Blog](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)

[Practical BM25 - Part 3: Considerations for Picking b and k1 in Elasticsearch | Elastic Blog](https://www.elastic.co/blog/practical-bm25-part-3-considerations-for-picking-b-and-k1-in-elasticsearch)

[tf-idf - 维基百科，自由的百科全书](https://zh.wikipedia.org/wiki/Tf-idf)

## Background

在 Elasticsearch 5.0 中，我们切换到 Okapi BM25 作为默认相似度算法，用于对搜索结果与查询的相关性进行评分。本文将着重介绍BM25 的实际应用，包括可用参数及其影响评分的因素。

### Understanding How Shards Affect Scoring

在学习 BM25 前，必须先理解 Elasticsearch 的索引可能被切成多个 shard（索引分片/物理分区）。因为 BM25 的相关性分数不是天然基于整个 index 的全局统计计算，而默认可能是在每个 shard 内部单独计算。shard 数量越多、数据越少，分数越容易出现偏差。

下面我们照搬参考网站的示例代码，目的是先创建一个 Elasticsearch 索引 `people`，再往里面插入几条测试文档，然后用同一个查询词 `"Shane"` 反复检索，观察 BM25 相关性分数如何随着文档数量和 shard 分布发生变化：

作者创建一个名为 `people` 的索引，并指定它有 5 个 primary shards，默认相关性算法使用 BM25：

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

作者使用它的名字做为示例：

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

找出 `title` 字段中匹配 `"Shane"` 的文档，自然会匹配到`/people/_doc/1`：

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

然后再次对它们做搜索：

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

也就是说现在有4条“文档”：

1. Shane
2. Shane C
3. Shane Connelly
4. Shane P Connelly

从其中，找出 `title` 字段中匹配 `"Shane"` 的文档。虽然说`title`字段都有`"Shane"`，但是它们的BM25分数不会一样。结果：`doc1` 和`doc3` 分数都是0.2876821，但`doc2` 分数是0.19856805，`doc4`分数是0.16853254。

尽管`doc2`和`doc3`很像，但是分数差了很多，这其实和"C"与"Connelly"的差异关系不大，而是和文档如何落在分片中有关。所以如何让分数更具一致性呢：

1. 数据量越大，shard 间的统计差异越小

2. 减少 shard 数量可以降低打分偏差

3. 如果想让多 shard 情况下的 BM25 打分更接近“全局统计”，可以在查询时加上 `?search_type=dfs_query_then_fetch`。它会先收集所有 shard 的词频统计信息，再统一计算分数，因此结果会接近甚至等同于 `number_of_shards=1` 时的分数。

   > `dfs_query_then_fetch` 的作用是先跨 shard 汇总词频统计，再统一计算 BM25 分数，使多 shard 的打分更接近单 shard 的全局效果；但它会增加一次额外通信，所以只有在小数据、多 shard、数据分布不均且很在意相关性分数时才值得使用。



## Algorithm and its variables

BM25 model:
$$
\sum_{i}^{n} IDF(q_i) \frac{f(q_i, D) * (k_1 + 1)}{f(q_i, D) + k_1 * (1 - b + b * \frac{fieldLen}{avgFieldLen})}
$$

- $q_i$: 查询中的第 $i$ 个关键词。
- $IDF(q_i)$: 关键词 $q_i$ 的逆文档频率（Inverse Document Frequency）。
- $f(q_i, D)$ :关键词 $q_i$ 在文档 $D$ 中的词频。
- **$fieldLen$**: 当前文档的长度。
- $avgFieldLen$: 索引中所有文档的平均长度。
- $k_1$ 和 $b$: 可调参数（通常 $k1 \in [1.2, 2.0]$，$b = 0.75$）。

其实简单来说，BM25就是引入了非线性，并解决了频次问题的TF-IDF模型。TF-IDF model:
$$
\text{Score} = f(q_i, D) \times \log\left(\frac{N}{n(q_i)}\right)
$$

#### $q_i$

例如，如果我搜索“shane”，这里只有一个查询词，因此 $q_0$ 就是“shane”。如果我用英文搜索“shane connelly”，Elasticsearch 会识别其中的空格，并将其分词（tokenize）为两个词项：$q_0$ 为“shane”，$q_1$ 为“connelly”。这些查询词会被代入公式的其他部分，最后将所有结果加总求和。

#### $IDF(q_i)$

公式中的 **IDF（逆文档频率）** 部分用于衡量一个词项在所有文档中出现的频率，并会对那些出现次数过多的常用词进行“**惩罚**”（即降低其权重）。在 Lucene/BM25 算法中，该部分的实际公式如下：
$$
\ln \left( 1 + \frac{(docCount - f(q_i) + 0.5)}{f(q_i) + 0.5} \right)
$$
其中，$docCount$ 是该分片中（如果使用的是 `search_type=dfs_query_then_fetch` 参数，则为跨所有分片）包含该字段值的文档总数；而 $f(q_i)$ 是包含第 $i$ 个查询词项的文档数量。在我们的示例中可以看到，“shane” 这个词在所有 4 个文档中都出现了，因此对于词项 “shane”，我们最终得到的逆文档频率 $IDF(\text{"shane"})$ 为：
$$
\ln\left(1 + \frac{(4 - 4 + 0.5)}{4 + 0.5}\right) = \ln\left(1 + \frac{0.5}{4.5}\right) = 0.105360515657826
$$
$IDF(\text{"connelly"})$为：
$$
\ln\left(1 + \frac{(4 - 2 + 0.5)}{2 + 0.5}\right) = \ln\left(1 + \frac{2.5}{2.5}\right) = 0.693147180559945
$$
我们可以看到，包含这些更罕见词项的查询（在我们的 4 文档语料库中，“connelly” 比 “shane” 更罕见）具有更高的**乘数**，因此它们对最终得分的贡献更大。这在直觉上是合理的：词项 “the” 可能出现在几乎每一篇英文文档中，所以当用户搜索像 “the elephant” 这样的内容时，“elephant” 显然比词项 “the”（几乎存在于所有文档中）更重要——我们也希望它能为搜索得分做出更多贡献。

#### $fieldLen/avgFieldLen$

档中的词项越多（至少是那些没匹配上查询条件的词项），该文档的得分就越低。同样，这在直觉上是合理的：如果一份文档长达 300 页且只提到了我的名字一次，那么它与我的相关性，很可能不如一条同样提到我一次的短推文。

#### $b$

如果 $b$ 的值越大，文档长度相对于平均长度所产生的影响就会被进一步放大。为了理解这一点，可以想象如果将 $b$ 设置为 0，长度比例的影响将完全消失，只受频次影响，文档的长度将对评分不产生任何影响。如果将 $b$ 设置为 1 ，则得分不受频次影响，只受长度比例的影响。

#### $f(q_i, D)$

这个值对应了 TF (Term Frequency, 词频) 

$f(q_i, D)$ 的含义是：“第 $i$ 个查询词项在文档 $D$ 中出现了多少次？”在所有这些文档中，$f(\text{"shane"}, D)$ 都是 1，但 $f(\text{"connelly"}, D)$ 各不相同：在文档 3 和 4 中是 1，但在文档 1 和 2 中是 0。如果有第 5 个文档的文本是 “shane shane”，那么它的 $f(\text{"shane"}, D)$ 就是 2。我们可以看到，$f(q_i, D)$ 同时出现在分子和分母中，此外还有一个特殊的 “$k_1$” 因子，我们稍后会讨论它。理解 $f(q_i, D)$ 的方式是：查询词项在文档中出现的次数越多，其得分就越高。这在直觉上是合理的：一个多次提到我们名字的文档，比只提到一次的文档更有可能与我们相关。

#### $k_1$

在 BM25 算法中，$k_1$ 是控制词频饱和度（Term Frequency Saturation）的核心参数。它通过为词频 $f(q_i, D)$ 对相关性得分的贡献设定渐近上限确保得分随词频增加而产生的边际增益呈非线性递减。相比于传统 TF-IDF 近乎线性的权重增长，这一机制有效抑制了高频词项（如关键词堆砌）对排名的过度干扰；其中，$k_1$ 的取值直接决定了得分趋于饱和的速度：较小的 $k_1$ 值会使词频贡献快速达到瓶颈，而较大的 $k_1$ 值则允许词频在更广的数值范围内维持显著的权重增益。

如果将 $k_1$ 设置为 0，得分将固定为1。如果将 $k_1$ 设置的很大（比如10000），公式近似退化为 $\frac{TF \times k_1}{k_1} = TF$ ，变成了词频本身。



## Picking $b$ and $k_1$

关于 $b$ 和 $k_1$ 的值，ES的文章也指出现在的值是个能涵盖多数情况的“经验值”，但是**不存在全局最优的 b 和 k1，只能结合语料和查询做实验评估。**

而且在检索性能不够好时，在调整 $b$ 和 $k_1$的值之前，应该先优化下面的内容：

1. 对精确短语匹配进行 boost；
2. 使用 synonyms 扩展用户可能感兴趣的同义表达；
3. 使用 fuzziness、typeahead、phonetic matching、stemming 等分析组件，处理拼写错误、语言差异和词形变化；
4. 使用 function score，根据发布时间、地理距离或业务特征调整文档得分。

至于后文ES的Explain API，不再赘述。