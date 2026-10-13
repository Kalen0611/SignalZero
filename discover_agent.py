
import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI
from discover_arxiv import search_recent_ai_papers
from arxiv_guard import validate_arxiv_report

load_dotenv()

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"]
)

MODEL = os.environ["LLM_MODEL"]



# 注册真实 Function Calling 工具
tools = [{
    "type": "function",
    "function": {
        "name": "discover_recent_ai_papers",
        "description": (
            "查询 arXiv 最近7天 AI Agent 领域的"
            "真实论文，返回标题、日期、摘要和链接"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    }
}]

messages = [
    {
        "role": "system",
        "content": (
            "你是 SignalZero，AI 前沿研究发现助手。"
            "需要发现新论文时，先调用检索工具。"
            "根据工具返回的标题和摘要，推荐最多3篇值得了解的论文。"
            "每篇解释：研究什么、为什么值得关注、涉及哪些专业概念。"
            "附上工具提供的原始论文链接和提交日期。"
            "不能编造论文或引用工具没有返回的链接。"
            "只能根据摘要判断潜在价值，不能声称研究结论已获验证。"
        )
    },
    {
        "role": "user",
        "content": (
            "帮我发现最近7天 AI Agent 领域"
            "值得了解的新研究，推荐最多3篇，"
            "用容易理解的中文解释。"
        )
    }
]

# 第一次请求：由 Qwen 选择工具
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=tools,
    tool_choice="auto",
    max_tokens=1000,
    extra_body={"enable_thinking": False}
)

message = response.choices[0].message

if not message.tool_calls:
    print("[提示] 模型没有调用发现工具")
    print(message.content or "无可见回答")

else:
    messages.append({
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            call.model_dump(exclude_none=True)
            for call in message.tool_calls
        ]
    })

    # 同一轮重复调用时，复用查询结果
    cached_papers = None

    for call in message.tool_calls:
        print("[模型请求工具]", call.function.name)

        if call.function.name != "discover_recent_ai_papers":
            result = {"error": "不允许调用未知工具"}
        else:
            try:
                if cached_papers is None:
                    cached_papers = search_recent_ai_papers()

                result = {
                    "source": "arXiv",
                    "papers": [
                        {
                            "title": p["title"],
                            "published": p["published"],
                            "url": p["url"],
                            "summary": p["summary"][:900]
                        }
                        for p in cached_papers
                    ]
                }

                print(
                    "[真实 arXiv 数据]",
                    len(result["papers"]),
                    "篇"
                )

            except Exception as exc:
                print("[工具执行失败]", type(exc).__name__)
                result = {
                    "error": "arXiv 查询暂时失败",
                    "papers": []
                }

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(
                result, ensure_ascii=False
            )
        })

    # 第二次请求：根据真实论文生成推荐
    final = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="none",
        max_tokens=1500,
        extra_body={"enable_thinking": False}
    )

    report = final.choices[0].message.content or ""

# 使用本次真实查询得到的论文链接作为允许集合
report = final.choices[0].message.content or ""

ok, reason = validate_arxiv_report(
    report,
    [p["url"] for p in (cached_papers or [])]
)

print("\n[arXiv 来源校验]")
print("通过：" + reason if ok else "失败：" + reason)

if ok:
    print("\n[SignalZero 前沿发现报告]")
    print(report)