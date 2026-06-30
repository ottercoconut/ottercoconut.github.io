+++

title = "RAGFlow切片策略解析"
date = 2026-04-14T20:06:34+08:00
lastmod = 2026-06-28T15:31:47+08:00
translationKey = "ragflow-chunking"
tags = ["RAG", "RAGFlow", "切片"]
categories = ["技术" ]

[params]
toc = true

+++

## RAGFlow 切片策略解析

众所周知RAGFlow是较早成熟且开源的RAG项目之一，近日笔者正在学习构建一个RAG项目，所以从RAGFlow的源码下手。首先学习的是它对markdown文件的解析方法和切片策略。

### `rag/app/naive.py`

`naive.py` 中支持很多文件的类型，比如`PDF`, `DOCX`, `Markdown`......

那么我们要学习的`markdown`类，主入口是`__call__()`，这是核心方法，编排了整个 Markdown 解析流程。

#### `__call()__`

```python
def __call__(self, filename, binary=None, separate_tables=True, delimiter=None, return_section_images=False):
```

| 参数                    | 类型  | 说明                                                   |
| :---------------------- | :---- | :----------------------------------------------------- |
| `filename`              | str   | 文件路径（当 `binary` 为空时用来读文件）               |
| `binary`                | bytes | 文件二进制内容，优先使用                               |
| `separate_tables`       | bool  | 是否将表格从正文中分离出来                             |
| `delimiter`             | str   | 自定义分割符，如果指定则用分割符切分而非按元素类型切分 |
| `return_section_images` | bool  | 是否额外返回每个 section 对应的图片                    |

**执行流程：**

```plaintext
Step 1: 文本解码
  ┌────────────────────────────┐
  │ binary → find_codec() →    │
  │ decode(encoding)           │
  │ 或 open(filename).read()   │
  └────────────┬───────────────┘
               ↓
Step 2: 表格提取（继承自父类）
  ┌────────────────────────────────────────────────────┐
  │ self.extract_tables_and_remainder(txt+"\n",         │
  │                           separate_tables)          │
  │ → (remainder, tables[])                             │
  │                                                     │
  │ 注意：这里传入的是 txt+"\n"（末尾补换行）             │
  └────────────┬───────────────────────────────────────┘
               ↓
Step 3: 元素扫描
  ┌────────────────────────────────────────────────────┐
  │ MarkdownElementExtractor(txt)                       │
  │   .extract_elements(delimiter, include_meta=True)   │
  │ → element_sections[]                                │
  │                                                     │
  │ ★ 关键：这里传入的是原始 txt，而非 remainder！        │
  │   （注释 L682-683 说明了原因：为避免重复表格）         │
  └────────────┬───────────────────────────────────────┘
               ↓
Step 4: 图片 URL 提取
  ┌────────────────────────────────────────────────────┐
  │ self.extract_image_urls_with_lines(txt)              │
  │ → image_refs = [{url, line}, ...]                   │
  └────────────┬───────────────────────────────────────┘
               ↓
Step 5: 元素-图片关联（核心融合逻辑）
  ┌────────────────────────────────────────────────────┐
  │ for element in element_sections:                    │
  │   ① 取 element 的 start_line ~ end_line            │
  │   ② 筛选行范围内的 image_refs                       │
  │   ③ load_images_from_urls() 下载图片（有缓存）      │
  │   ④ 多张图用 concat_img 合并为一张                  │
  │   ⑤ sections.append((content, ""))                  │
  │   ⑥ section_images.append(combined_image or None)   │
  └────────────┬───────────────────────────────────────┘
               ↓
Step 6: 表格后处理
  ┌────────────────────────────────────────────────────┐
  │ for table in tables:                                │
  │   markdown(table, extensions=["tables"]) → html     │
  │   tbls.append(((None, html), ""))                   │
  └────────────┬───────────────────────────────────────┘
               ↓
Step 7: 返回结果
  ┌────────────────────────────────────────────────────┐
  │ if return_section_images:                           │
  │   return sections, tbls, section_images             │
  │ else:                                               │
  │   return sections, tbls                             │
  └────────────────────────────────────────────────────┘

```

**输出数据结构：**

```python
sections = [
    ("## 标题\n正文内容...", ""),      # (文本, 位置标签—永远为空字符串)
    ("```python\ncode\n```", ""),       # 代码块
    ...
]

tbls = [
    ((None, "<table>...</table>"), ""),  # (None, HTML表格字符串)
    ...
]

section_images = [
    PIL.Image,    # 该 section 中所有图片合并后的图像对象
    None,         # 该 section 无图片
    PIL.Image,
    ...
]
```

这其中最关键的是**表格提取**和**元素扫描**的部分：

#### `extract_tables_and_remainder()`

这个方法定义于`deepdoc/parser/resume/markdown_parser.py`的`RAGFlowMarkdownParser`类中，用于将markdown中的表格提取出来

```python
class RAGFlowMarkdownParser:
    def __init__(self, chunk_token_num=128):
        self.chunk_token_num = int(chunk_token_num)

    def extract_tables_and_remainder(self, markdown_text, separate_tables=True):
        # 返回: (剩余正文, [表格列表])
```

**表格识别策略：**

| 类型                 | 正则                                               | 示例                                   |
| :------------------- | :------------------------------------------------- | :------------------------------------- |
| 有边框 Markdown 表格 | `|...|...|` + `|---|` 分隔行 + 数据行              | `| A | B |`                            |
| 无边框 Markdown 表格 | `text|text` + 分隔行 + 数据行                      | `Col1 | Col2`                          |
| HTML 表格            | `<table>...</table>`，支持包裹在 `<html><body>` 中 | `<table><tr><td>...</td></tr></table>` |

当 `separate_tables=True` 时，表格从正文里移除并单独返回；为 `False` 时则就地转为 HTML。

#### `MarkdownElementExtractor`

该类位于`deepdoc/parser/markdown_parser.py`，实现了一个简易的 Markdown 元素识别器，将文本按行扫描并归类为不同的块类型。

```python
class MarkdownElementExtractor:
    def __init__(self, markdown_content):
        self.markdown_content = markdown_content
        self.lines = markdown_content.split("\n")

    def extract_elements(self, delimiter=None, include_meta=False):
        """提取各种元素(headers, code blocks, lists, 等)"""

```

**输出元素结构：**

```python
{
    "type": "header" | "code_block" | "list_block" | "blockquote" | "text_block",
    "content": "具体文本内容",
    "start_line": 0,   # 起始行号
    "end_line": 5,      # 结束行号
}

```

- `_extract_header()` : 返回单行的"header"
- `_extract_code_block()` : 直到遇到" ``` "返回多行的代码块"code_block"
- `_extract_list_block()` : 吞入满足以下条件的行：
  - 以 `-`, `*`, `+` 或 `数字.` 开头（列表项）
  - 空行（列表项间隙）
  - 以 2+ 空格缩进的子列表或续行
- `_extract_blockquote()` : 持续吞入">"开头的行或内部的空行
- `_extract_text_block()` : 处理不属于上面几种类型的普通文本"text_block"，直到符合上面类型的元素再次出现

#### `extract_image_urls_with_lines()`

这个方法用于找出 Markdown 文本中所有图片引用及其所在行号。行号用于后续将图片关联到对应的 section。

**三阶段提取策略：**

```plaintext
阶段 1: Markdown 语法图片

  正则: ![alt](url)  →  提取 url

  模式: r"!\[[^\]]*\]\(([^)\s]+)"

阶段 2: HTML 内联图片（单行）

  正则: src="url" / src='url'  →  提取 url

  模式: r'src=["\\\'"]([^"\\\'>\\s]+)'

阶段 3: HTML 跨行图片（BeautifulSoup 兜底）

  解析整个文本为 HTML，查找所有 <img> 标签的 src

  通过字符偏移量计算行号

  用 seen 集合避免与阶段 1/2 重复
```

**返回值：**

```python
[
    {"url": "https://example.com/img.png", "line": 5},
    {"url": "./assets/diagram.svg", "line": 12},
    ...
]
```

#### `load_images_from_urls()`

```python
def load_images_from_urls(self, urls, cache=None):
    # 返回: (images[], cache{})
```

| 功能      | 细节                                                         |
| :-------- | :----------------------------------------------------------- |
| HTTP 图片 | `requests.get(url, timeout=30)`，校验 `Content-Type` 为 `image/` |
| 本地图片  | `Path(url).exists()` 检查后用 `PIL.Image.open()`             |
| 缓存机制  | `cache` dict 避免重复下载同一 URL                            |
| 统一格式  | 所有图片转为 `RGB` 模式 (`convert("RGB")`)                   |
| 错误处理  | 失败时 `cache[url] = None`，不中断流程                       |

这里的思路比较朴素，但很实用：

1. 先根据 `url` 判断是网络图片还是本地图片
2. 统一加载成 `PIL.Image`
3. 放入缓存，避免同一张图在多个 section 中重复读取
4. 后续如果某个 section 对应多张图片，再交给 `concat_img` 合并

也就是说，RAGFlow 在 Markdown 中并不是把每一张图片都单独当成一个 chunk，而是先尝试把**同一个 section 内的图片聚合**起来，再与文本一起进入后续流程。

#### `urls_in_section = [...]`

在 `Markdown.__call__()` 中，真正把文本 section 和图片联系起来的代码是这一段：

```python
for element in element_sections:
    content = element["content"]
    start_line = element["start_line"]
    end_line = element["end_line"]
    urls_in_section = [ref["url"] for ref in image_refs if start_line <= ref["line"] <= end_line]
```

其核心思想非常直接：**按行号做区间归属**。

- 一个 Markdown 元素先被标记 `start_line` 和 `end_line`
- 所有图片引用也带有自己的 `line`
- 只要图片所在行落在元素区间内，就认为这张图属于这个 section

这是一种很工程化的做法。它不追求复杂语义理解，而是利用 Markdown 本身“按行组织”的特点，以较低成本建立图文关联。

例如下面这段 Markdown：

```markdown

### 模型结构

这里介绍整体流程。

![pipeline](./pipeline.png)

接着说明各模块职责。
```

如果这一整段被 `MarkdownElementExtractor` 视为同一个 `text_block`，那么图片就会和这一段正文绑定在一起；如果标题和正文被分成两个元素，则图片通常会归到正文所在的 section，而不会归到标题 section。

#### 表格处理细节

前面提到，`Markdown.__call__()` 中虽然调用了：

```python
remainder, tables = self.extract_tables_and_remainder(f"{txt}\n", separate_tables=separate_tables)
```

但后面真正做元素扫描时，使用的是：

```python
extractor = MarkdownElementExtractor(txt)
```

而不是 `remainder`。

源码里其实已经留了注释：

```python
# To eliminate duplicate tables in chunking result, uncomment code below and set separate_tables to True ...
# extractor = MarkdownElementExtractor(remainder)
extractor = MarkdownElementExtractor(txt)
```

这说明作者其实也意识到了一个现象：**表格可能同时出现在 section chunk 和 table result 中**。

从实现角度看，这未必是 bug，更像是一种偏保守的召回策略：

- 正文 chunk 中保留表格原始上下文
- `tables` 中再额外保留结构化表格内容

这样做可能带来一定冗余，但也提高了检索时命中表格信息的概率。

### `chunk()`

看到这里，其实还只是完成了解析和预处理。真正决定最终 chunk 长什么样的，不在 `Markdown.__call__()`，而在 `rag/app/naive.py` 下面的 `chunk()` 函数里。

Markdown 文件分支一开始会先调用前面的解析器：

```python
markdown_parser = Markdown(int(parser_config.get("chunk_token_num", 128)))
sections, tables, section_images = markdown_parser(
    filename,
    binary,
    separate_tables=False,
    delimiter=parser_config.get("delimiter", "\n!?;。；！？"),
    return_section_images=True,
)
```

这里有两个细节值得注意：

- `return_section_images=True`
  说明 Markdown 解析阶段生成的图片不会丢，而是继续带到后面的 chunk 合并流程中。
- `separate_tables=False`
  说明这里并没有把表格完全从正文切走，而是倾向于让表格继续留在 Markdown 上下文里，同时又额外生成 `tables` 供表格索引使用。

接着，如果当前租户存在 `IMAGE2TEXT` 模型，`chunk()` 会尝试给 Markdown 中的图片补一段描述文本：

```python
try:
    vision_model_config = get_tenant_default_model_by_type(kwargs["tenant_id"], LLMType.IMAGE2TEXT)
    vision_model = LLMBundle(kwargs["tenant_id"], vision_model_config)
except Exception as e:
    logging.warning(f"Failed to detect figure extraction: {e}")
    vision_model = None
```

如果视觉模型可用，则继续遍历每个 section：

```python
for idx, (section_text, _) in enumerate(sections):
    images = []
    if section_images and len(section_images) > idx and section_images[idx] is not None:
        images.append(section_images[idx])

    if images and len(images) > 0:
        combined_image = reduce(concat_img, images) if len(images) > 1 else images[0]
        markdown_vision_parser = VisionFigureParser(
            vision_model=vision_model,
            figures_data=[((combined_image, ["markdown image"]), [(0, 0, 0, 0, 0)])],
            **kwargs
        )
        boosted_figures = markdown_vision_parser(callback=callback)
        sections[idx] = (
            section_text + "\n\n" + "\n\n".join([fig[0][1] for fig in boosted_figures]),
            sections[idx][1]
        )
```

这里可以看出 Markdown 图片增强的几个特点：

- 粒度是 **section 级别**
- 输入图片是前面已经聚合好的 `section_images[idx]`
- 输出不是新的 chunk，而是把图片描述文本直接追加回原 `section_text`

#### `VisionFigureParser`

该类定义在 `deepdoc/parser/figure_parser.py` 中：

```python
class VisionFigureParser:
    def __init__(self, vision_model, figures_data, *args, **kwargs):
        self.vision_model = vision_model
        self.figure_contexts = kwargs.get("figure_contexts") or []
        self.context_size = max(0, int(kwargs.get("context_size", 0) or 0))
        self._extract_figures_info(figures_data)
```

这个类的职责并不复杂，可以理解为一个“图片描述批处理器”：

- 接收图片列表 `figures_data`
- 整理出图片、描述、位置信息
- 调用视觉模型生成描述
- 再把结果重新组装回原来的数据结构

Markdown 分支给它传入的 `figures_data` 形式是：

```python
[((combined_image, ["markdown image"]), [(0, 0, 0, 0, 0)])]
```

也就是说，每次只处理当前 section 对应的一张聚合图，原始描述先放一个占位值 `"markdown image"`，位置则放一个 dummy tuple。

#### `_extract_figures_info()`

这个方法负责把 `figures_data` 拆成内部使用的三个列表：

```python
def _extract_figures_info(self, figures_data):
    self.figures = []
    self.descriptions = []
    self.positions = []
```

其中核心分支是：

```python
if len(item) == 2 and isinstance(item[0], tuple) and len(item[0]) == 2:
    img_desc = item[0]
    img = ensure_pil_image(img_desc[0])
    self.figures.append(img)
    self.descriptions.append(img_desc[1])
    self.positions.append(item[1])
```

因此传入的：

```python
((combined_image, ["markdown image"]), [(0, 0, 0, 0, 0)])
```

会被拆成：

- `self.figures` : `[combined_image]`
- `self.descriptions` : `[["markdown image"]]`
- `self.positions` : `[[(0, 0, 0, 0, 0)]]`

这里的 `ensure_pil_image()` 负责把输入统一成 `PIL.Image` 对象，因此前面无论传入的是普通图片对象还是惰性图片对象，到了这里都会被标准化。

#### `__call__()`

`VisionFigureParser.__call__()` 才是真正执行视觉增强的入口：

```python
def __call__(self, **kwargs):
    callback = kwargs.get("callback", lambda prog, msg: None)
```

它内部先定义了一个 `process()`，用于处理单张图片：

```python
def process(figure_idx, figure_binary):
    context_above = ""
    context_below = ""
    if figure_idx < len(self.figure_contexts):
        context_above, context_below = self.figure_contexts[figure_idx]
    if context_above or context_below:
        prompt = vision_llm_figure_describe_prompt_with_context(
            context_above=context_above,
            context_below=context_below,
        )
    else:
        prompt = vision_llm_figure_describe_prompt()
```

然后通过线程池并发调用：

```python
for idx, img_binary in enumerate(self.figures or []):
    futures.append(shared_executor.submit(process, idx, img_binary))
```

等所有任务完成之后，将返回的描述文本写回：

```python
for future in as_completed(futures):
    figure_num, txt = future.result()
    if txt:
        self.descriptions[figure_num] = txt + "\n".join(self.descriptions[figure_num])
```

最后再调用 `_assemble()` 重新组装：

```python
self._assemble()
return self.assembled
```

对于 Markdown 分支来说，这里有两个细节：

- 没有显式传入 `figure_contexts`，因此默认使用 `vision_llm_figure_describe_prompt()`
- 回填时会把模型输出和原始描述拼在一起，因此最终描述中理论上可能保留 `"markdown image"` 这个占位文本

#### `picture_vision_llm_chunk()`

`process()` 里真正调用视觉模型的函数是 `rag/app/picture.py` 中的：

```python
def vision_llm_chunk(binary, vision_model, prompt=None, callback=None):
```

虽然名字叫 `vision_llm_chunk`，但其作用其实很直接，就是把图片交给 VLM 并返回描述文本。

其主要步骤如下：

```python
with io.BytesIO() as img_binary:
    try:
        img.save(img_binary, format="JPEG")
    except Exception:
        img_binary.seek(0)
        img_binary.truncate()
        img.save(img_binary, format="PNG")

    img_binary.seek(0)
    ans = clean_markdown_block(vision_model.describe_with_prompt(img_binary.read(), prompt))
    txt += "\n" + ans
    return txt
```

这里做了几件事：

- 先把 `PIL.Image` 编码成二进制
- 优先尝试保存为 `JPEG`，失败则退回 `PNG`
- 调用 `vision_model.describe_with_prompt()` 生成描述
- 用 `clean_markdown_block()` 清理模型输出中的 Markdown 包裹

因此这个函数返回的是一段纯文本，而不是结构化对象。

#### `vision_llm_figure_describe_prompt()`

在 `VisionFigureParser.__call__()` 中，无上下文情况下使用的是：

```python
prompt = vision_llm_figure_describe_prompt()
```

而如果存在上下文，则切换到：

```python
prompt = vision_llm_figure_describe_prompt_with_context(
    context_above=context_above,
    context_below=context_below,
)
```

这两组 prompt 都定义在 `rag/prompts/` 下。其核心约束是：

- 只根据图中可见内容生成文本
- 如果是表格、柱状图、折线图这类“可枚举数据图”，则按固定字段输出
- 如果不是结构化数据图，则按空间顺序描述可见内容
- 不允许额外推断流程、功能或语义

也就是说，这一步生成的不是泛化摘要，而是偏向**检索友好**的图片文本表示。

#### `sections[idx] = (...)`

最终在 `rag/app/naive.py` 中，增强结果是这样写回 section 的：

```python
sections[idx] = (
    section_text + "\n\n" + "\n\n".join([fig[0][1] for fig in boosted_figures]),
    sections[idx][1]
)
```

因此 Markdown 图像增强不会引入新的切片层级，而是把图片描述文本直接拼回现有 section。

在这一轮增强之后，`chunk()` 才会真正进入 Markdown 专属的 chunk 合并逻辑：

```python
if is_markdown:
    merged_chunks = []
    merged_images = []
    chunk_limit = max(0, int(parser_config.get("chunk_token_num", 128)))

    current_text = ""
    current_tokens = 0
    current_image = None

    for idx, sec in enumerate(sections):
        text = sec[0] if isinstance(sec, tuple) else sec
        sec_tokens = num_tokens_from_string(text)
        sec_image = section_images[idx] if section_images and idx < len(section_images) else None
```

这段代码表明，Markdown 的切片单位不是“原始全文直接按分隔符硬切”，而是：

```plaintext
Markdown 文本
  ↓
按元素扫描成多个 section
  ↓
每个 section 绑定对应图片
  ↓
图片描述增强（如果启用）
  ↓
按 token 上限逐个累积合并
  ↓
得到最终 chunk
```

RAGFlow 对 Markdown 没有直接调用通用的 `naive_merge_with_images()`，而是单独写了一套更简单的逻辑。其规则是：

- 如果加入下一个 section 后仍未超过 `chunk_token_num`，则继续追加
- 如果会超过上限，就先把当前 chunk 落盘，再开启一个新的 chunk
- 如果开启新 chunk 时配置了 `overlapped_percent`，则保留上一 chunk 尾部的一部分文本作为重叠上下文
- 与此同时，当前 chunk 内涉及的所有图片会被不断 `concat_img` 合并

关键代码如下：

```python
if current_text and current_tokens + sec_tokens > chunk_limit:
    merged_chunks.append(current_text)
    merged_images.append(current_image)
    overlap_part = ""
    if overlapped_percent > 0:
        overlap_len = int(len(current_text) * overlapped_percent / 100)
        if overlap_len > 0:
            overlap_part = current_text[-overlap_len:]
    current_text = overlap_part
    current_tokens = num_tokens_from_string(current_text)
    current_image = current_image if overlap_part else None
```

这里可以看出两个特点：

- 重叠是按**字符长度**截尾，而不是按 section 粒度重叠
- 图片是按 chunk 聚合的，只要 section 被并入同一个 chunk，其图片也会被拼到同一张图上

因此，一个最终的 Markdown chunk，本质上是：

```python
{
    "text": "若干相邻 section 合并后的文本",
    "image": "这些 section 内图片拼接后的结果（如果有）"
}
```

在 chunk 合并完成之后，RAGFlow 会根据该批 chunk 是否含图走两条不同路径：

```python
has_images = merged_images and any(img is not None for img in merged_images)

if has_images:
    res.extend(tokenize_chunks_with_images(chunks, doc, is_english, merged_images, child_delimiters_pattern=child_deli))
else:
    res.extend(tokenize_chunks(chunks, doc, is_english, pdf_parser, child_delimiters_pattern=child_deli))
```

其中：

- `tokenize_chunks()` 负责纯文本 chunk 的分词和字段封装
- `tokenize_chunks_with_images()` 则会把对应图片写入文档对象的 `image` 字段
- 表格则另外通过 `tokenize_table(tables, doc, is_english)` 进入结果集

也就是说，Markdown 在 RAGFlow 中最后会被拆成三类可检索对象：

1. 普通文本 chunk
2. 携带图片的多模态 chunk
3. 表格对象

### 小结

至此，RAGFlow 对 Markdown 的“切片”逻辑就比较清楚了。它并不是简单地按固定长度裁文本，而是分成了几层：

1. 先识别表格、标题、代码块、列表、引用块和普通文本块
2. 再根据图片引用所在行号，把图片绑定到对应 section
3. 然后按 token 上限把多个相邻 section 合并为 chunk
4. 最后把文本、图片、表格分别包装成可检索对象

从工程实现上看，这套方案的优点是：

- 实现简单，可维护性高
- 比纯分隔符切片更保留 Markdown 结构
- 能较自然地支持图文混合检索
- 表格被单独抽出后，也便于做专门处理

当然，它也有一些局限，例如：

- 图片归属依赖行号，精度有限
- section 的粒度较粗，未做更深层的语义切分
- 表格与正文可能存在信息重复

但对一个通用 RAG 系统来说，这样的取舍是相当合理的。它没有追求复杂而昂贵的 Markdown AST 解析，而是用较低复杂度完成了“结构感知切片”。

笔者认为，这也是 RAGFlow 值得学习的一点：很多时候，切片策略不一定要非常“聪明”，但一定要足够稳定、可解释，并且方便与后续检索流程对接。
