# SignalZero — AI Research Discovery & Source Tracing Agent

SignalZero 是一个基于 Python、LLM Function Calling、arXiv 和 Crossref API 构建的学术信息发现与溯源智能体。项目通过 OpenAI 兼容接口调用大语言模型，实现自主工具选择、真实数据检索、研究信息总结及引用来源一致性校验。当前已使用通义千问完成运行验证。架构可扩展至其他支持 Function Calling 的兼容模型服务，但尚未逐一验证。

项目旨在帮助用户发现近期 AI 研究、查找真实学术出版记录，并通过来源一致性检查降低模型引用未经检索资料的风险。

## 核心功能

### 1. 学术信息溯源（Source Tracing）

- 用户可以自行输入感兴趣的研究主题。
- 通义千问通过 Function Calling 请求 Crossref 检索工具。
- Python 获取真实学术出版元数据，包括标题、DOI、日期和链接。
- 支持多轮工具调用。
- 检查报告中的 DOI 是否来自本轮工具检索结果。

### 2. 前沿研究发现（Research Discovery）

- 从 arXiv 获取最近 7 天符合指定检索条件的 AI Agent 相关论文。
- 通义千问根据论文标题和摘要推荐值得了解的研究。
- 使用中文解释研究主题、潜在价值与专业术语。
- 检查报告引用的 arXiv 论文编号是否来自本轮检索结果。

## 技术栈

- Python
- Qwen / 阿里云百炼 API
- Function Calling
- OpenAI-compatible Python SDK
- Crossref API
- arXiv API
- unittest

## 项目文件

| 文件 | 功能 |
|---|---|
| `first_tool.py` | 学术信息溯源 Agent |
| `discover_agent.py` | AI 前沿研究发现 Agent |
| `discover_arxiv.py` | arXiv 数据检索 |
| `source_guard.py` | DOI 来源一致性校验 |
| `arxiv_guard.py` | arXiv 论文引用校验 |
| `test_source_guard.py` | DOI 校验测试 |
| `test_arxiv_guard.py` | arXiv 校验测试 |

## 安装与运行

**1. 安装依赖**

`python -m pip install -r requirements.txt`

**2. 配置环境**

复制 `.env.example` 为 `.env`，填入自己的 API Key、模型名称及对应服务地址。

**3. 运行信息溯源功能**

`python first_tool.py`

根据提示输入需要研究的话题。

**4. 运行前沿研究发现功能**

`python discover_agent.py`

## 自动化测试

执行：

`python -m unittest -v test_source_guard.py test_arxiv_guard.py`

当前已在本地运行通过 6 个来源一致性单元测试，覆盖有效引用、未知引用和缺少引用的情况。

## 当前限制

- 项目目前是学习与工程实践原型，并非生产级信息核验系统。
- Crossref 元数据不等同于论文全文或研究结论。
- 来源一致性校验只能确认引用来自本轮工具结果，不能证明论文结论正确。
- arXiv 发现功能目前只检索有限范围的论文，不能保证覆盖全部重要研究。
- 外部 API 可能出现请求限制、超时或服务异常。

## 开发说明

本项目采用 AI 辅助开发方式：AI 参与代码实现和问题排查，开发者负责项目需求选择、实际运行、测试验证及调试。

项目重点展示大模型工具调用、外部 API 集成、来源校验和基本自动化测试能力。