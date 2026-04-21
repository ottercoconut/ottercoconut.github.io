+++

title = "RAGFlow切片策略解析"
date = 2026-04-14T20:06:34+08:00
translationKey = "ragflow-chunking"
tags = ["切片",]
categories = ["技术", "RAG"]

[params]
toc = true

+++

# RAGFlow 切片策略解析

众所周知RAGFlow是较早成熟且开源的RAG项目之一，近日笔者正在学习构建一个RAG项目，所以从RAGFlow的源码下手。首先学习的是它对markdown文件的解析方法和切片策略。

## `rag/app/naive.py`

`naive.py` 中支持很多文件的类型，比如`PDF`, `DOCX`, `Markdown`......

那么我们要学习的`markdown`类，主入口是`__call__()`，这是核心方法，编排了整个 Markdown 解析流程。

### `__call()__`

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

### `extract_image_urls_with_lines()`

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

### `load_images_from_urls()`

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
