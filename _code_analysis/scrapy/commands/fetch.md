# `scrapy/commands/fetch.py`

⬜ **待分析**

---

## 📁 文件信息

| 项目 | 内容 |
|------|------|
| **文件路径** | `scrapy/commands/fetch.py` |
| **模块用途** | `scrapy fetch` 命令的实现——使用 Scrapy 下载器获取 URL 并输出内容到 stdout |
| **核心类** | `Command`（继承 `ScrapyCommand`） |
| **依赖关键模块** | `w3lib.url.is_url`, `SequenceExclude`, `spidercls_for_request` |
| **行数** | 99 |

---

## 📥 导入区（L1–L17）

```python
 1: from __future__ import annotations
 2: 
 3: import sys
 4: from argparse import Namespace  # noqa: TC003
 5: from typing import TYPE_CHECKING, Any
 6: 
 7: from w3lib.url import is_url
 8: 
 9: from scrapy.commands import ScrapyCommand
10: from scrapy.exceptions import UsageError
11: from scrapy.http import Request, Response
12: from scrapy.utils.datatypes import SequenceExclude
13: from scrapy.utils.spider import DefaultSpider, spidercls_for_request
14: 
15: if TYPE_CHECKING:
16:     from argparse import ArgumentParser
17:     from collections.abc import AsyncIterator
18: 
19:     from scrapy import Spider
```

| 行号 | 标识符 | 说明 |
|------|--------|------|
| 1 | `from __future__ import annotations` | 启用 PEP 604，注解延迟求值 |
| 3 | `sys` | `sys.stdout.buffer.write()` 直接输出字节到 stdout |
| 4 | `Namespace` | 类型注解，`# noqa: TC003` 避免类型检查导入报警 |
| 5 | `TYPE_CHECKING, Any` | 类型注解 |
| 7 | `is_url` | URL 格式校验 |
| 9 | `ScrapyCommand` | 命令基类 |
| 10 | `UsageError` | 参数错误异常 |
| 11 | `Request, Response` | Scrapy HTTP 请求/响应 |
| 12 | `SequenceExclude` | 反向范围选择器——排除 3xx 状态码 |
| 13 | `DefaultSpider, spidercls_for_request` | 默认 spider + 根据请求自动匹配 spider 类 |
| 15–19 | `TYPE_CHECKING` 块 | 仅在静态类型检查时导入 |

---

## 类：Command（L19–L99）

### 骨架（先览）

```python
 19: class Command(ScrapyCommand):
 20:     def syntax(self) -> str:
 21:         return "[options] <url>"
 23:     def short_desc(self) -> str:
 24:         return "Fetch a URL using the Scrapy downloader"
 26:     def long_desc(self) -> str:
 31:     def add_options(self, parser: ArgumentParser) -> None:
 42:     def _print_headers(self, headers, prefix) -> None:
 46:     def _print_response(self, response, opts) -> None:
 53:     def _print_bytes(self, bytes_) -> None:
 56:     def run(self, args, opts) -> None:
```

- 继承 `ScrapyCommand`，无需项目环境（`requires_project` 默认 `False`）
- 3 个私有方法处理输出格式 + `run()` 核心逻辑
- 支持 `--spider`、`--headers`、`--no-redirect` 选项

### 详细分析

```python
19: class Command(ScrapyCommand):
20:     def syntax(self) -> str:
21:         return "[options] <url>"
22: 
23:     def short_desc(self) -> str:
24:         return "Fetch a URL using the Scrapy downloader"
25: 
26:     def long_desc(self) -> str:
27:         return (
28:             "Fetch a URL using the Scrapy downloader and print its content"
29:             " to stdout. You may want to use --nolog to disable logging"
30:         )
31: 
32:     def add_options(self, parser: ArgumentParser) -> None:
33:         super().add_options(parser)
34:         parser.add_argument("--spider", dest="spider", help="use this spider")
35:         parser.add_argument(
36:             "--headers",
37:             dest="headers",
38:             action="store_true",
39:             help="print response HTTP headers instead of body",
40:         )
41:         parser.add_argument(
42:             "--no-redirect",
43:             dest="no_redirect",
44:             action="store_true",
45:             default=False,
46:             help="do not handle HTTP 3xx status codes and print response as-is",
47:         )
```

| 行号 | 说明 |
|------|------|
| 19 | 继承 `ScrapyCommand` |
| 20–21 | `syntax()`——`[options] <url>` |
| 23–24 | `short_desc()`——"Fetch a URL using the Scrapy downloader" |
| 26–30 | `long_desc()`——提示可用 `--nolog` 禁用日志 |
| 32 | `add_options()`——添加命令特有选项 |
| 33 | 调用父类添加全局选项 |
| 34 | `--spider`——指定使用哪个 spider |
| 35–40 | `--headers`——输出 HTTP 请求/响应头而非 body |
| 41–47 | `--no-redirect`——不自动处理 3xx 重定向，直接输出原始响应 |

```python
49:     def _print_headers(self, headers: dict[bytes, list[bytes]], prefix: bytes) -> None:
50:         for key, values in headers.items():
51:             for value in values:
52:                 self._print_bytes(prefix + b" " + key + b": " + value)
53: 
54:     def _print_response(self, response: Response, opts: Namespace) -> None:
55:         if opts.headers:
56:             assert response.request
57:             self._print_headers(response.request.headers, b">")
58:             print(">")
59:             self._print_headers(response.headers, b"<")
60:         else:
61:             self._print_bytes(response.body)
62: 
63:     def _print_bytes(self, bytes_: bytes) -> None:
64:         sys.stdout.buffer.write(bytes_ + b"\n")
```

| 行号 | 说明 |
|------|------|
| 49–52 | `_print_headers()`——逐行输出请求/响应头，每行带 `>`（请求）或 `<`（响应）前缀 |
| 54–61 | `_print_response()`——`--headers` 模式输出头信息，否则输出 body |
| 56 | `assert response.request`——确保 request 存在（正常情况下总是成立） |
| 57–59 | 输出格式：`> Header: value` → 空行 → `< Header: value` |
| 63–64 | `_print_bytes()`——直接向 `sys.stdout.buffer` 写入字节，避免编码转换 |

```python
66:     def run(self, args: list[str], opts: Namespace) -> None:
67:         if len(args) != 1 or not is_url(args[0]):
68:             raise UsageError
69:         request = Request(
70:             args[0],
71:             callback=self._print_response,
72:             cb_kwargs={"opts": opts},
73:             dont_filter=True,
74:         )
75:         # by default, let the framework handle redirects,
76:         # i.e. command handles all codes expect 3xx
77:         if not opts.no_redirect:
78:             request.meta["handle_httpstatus_list"] = SequenceExclude(range(300, 400))
79:         else:
80:             request.meta["handle_httpstatus_all"] = True
81: 
82:         spidercls: type[Spider] = DefaultSpider
83:         assert self.crawler_process
84:         spider_loader = self.crawler_process.spider_loader
85:         if opts.spider:
86:             spidercls = spider_loader.load(opts.spider)
87:         else:
88:             spidercls = spidercls_for_request(spider_loader, request, spidercls)
89: 
90:         async def start(self: Spider) -> AsyncIterator[Any]:
91:             yield request
92: 
93:         spidercls.start = start  # type: ignore[method-assign]
94: 
95:         self.crawler_process.crawl(spidercls)
96:         self.crawler_process.start()
```

| 行号 | 说明 |
|------|------|
| 66 | `run()`——命令执行入口 |
| 67–68 | **URL 校验**——必须且只能传 1 个参数，且必须是合法 URL |
| 69–74 | 创建 `Request` 对象：`callback=self._print_response`（响应直接输出）、`dont_filter=True`（不判重） |
| 75–78 | **默认行为**：用 `SequenceExclude(range(300, 400))` 让框架自动处理 3xx 重定向 |
| 79–80 | `--no-redirect`：`handle_httpstatus_all=True` 让所有状态码都进入 callback |
| 82 | 默认使用 `DefaultSpider` |
| 83–84 | 断言 + 获取 spider_loader |
| 85–86 | `--spider` 指定：加载指定 spider |
| 87–88 | 未指定：用 `spidercls_for_request()` 根据 URL 自动匹配 spider |
| 90–91 | **动态定义 `start()` 协程**——yield 该请求 |
| 93 | **动态注入 `start()`**——覆盖 spider 类的 start 方法 |
| 95–96 | 注册爬虫 + 启动爬虫循环（阻塞） |

---

## 🔄 执行流程（Mermaid 时序图）

```mermaid
sequenceDiagram
    participant CLI as scrapy fetch
    participant Cmd as Command.run()
    participant CP as CrawlerProcess
    participant SL as SpiderLoader
    participant SP as Spider
    participant DW as Downloader

    CLI->>Cmd: run(args, opts)
    Cmd->>Cmd: 校验 args == 1 且是合法 URL
    Cmd->>Cmd: 创建 Request(callback=_print_response)
    alt --no-redirect
        Cmd->>Cmd: handle_httpstatus_all = True
    else 默认
        Cmd->>Cmd: handle_httpstatus_list = SequenceExclude(300-399)
    end
    opt --spider 指定
        Cmd->>SL: load(spidername)
        SL-->>Cmd: spidercls
    else 未指定
        Cmd->>SL: spidercls_for_request(url)
        SL-->>Cmd: DefaultSpider / 匹配的 spider
    end
    Cmd->>SP: 动态注入 start() 协程
    Cmd->>CP: crawl(spidercls)
    Cmd->>CP: start()
    CP->>SP: start()
    SP-->>CP: Request
    CP->>DW: 下载
    DW-->>CP: Response
    CP->>SP: callback = _print_response
    SP->>Cmd: _print_response(response, opts)
    alt --headers
        Cmd->>Cmd: 输出 > Header: value
        Cmd->>Cmd: 输出 < Header: value
    else
        Cmd->>Cmd: 输出 response.body
    end
    CP-->>Cmd: 爬取完成
```

---

## ⚠️ 关键点与陷阱

### 关键点

1. **`is_url()` 校验**（L67）
   - 使用 `w3lib.url.is_url()` 校验参数格式，非法 URL 直接抛 `UsageError`

2. **`SequenceExclude` 反向范围**（L78）
   - `SequenceExclude(range(300, 400))` 表示"处理所有非 3xx 状态码"，3xx 由框架自动重定向

3. **动态注入 `start()` 方法**（L90-93）
   - 与 `check.py` 相同的模式：在 `run()` 内定义协程，注入到 spider 类

4. **`sys.stdout.buffer` 字节直写**（L64）
   - 不使用 `print()` 避免编码问题，直接向缓冲写入字节

5. **`spidercls_for_request()` 自动匹配**（L88）
   - 根据 URL 自动选择适当的 spider，未指定 `--spider` 时使用

### 陷阱

1. **`--no-redirect` 与 `SequenceExclude` 互斥**
   - 两个分支互斥：默认用 `SequenceExclude` 控制框架处理重定向，`--no-redirect` 则接管所有状态码

2. **`assert response.request`（L56）**
   - 仅在 `--headers` 模式触发。正常情况下 Response 总是绑定了对应的 Request

3. **`args[0]` 不检查是否为文件路径**
   - 只检查 `is_url()`，传本地文件路径不会报正确错误消息

4. **`# noqa: TC003`（L4）**
   - `Namespace` 在运行时不会被用到（仅类型注解），但 `from argparse import Namespace` 是顶层导入，`TC003` 标记此行为"不必要的类型检查导入"但为了签名兼容保留
