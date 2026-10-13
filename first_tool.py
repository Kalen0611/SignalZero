
import os
import json
import requests
import time
from dotenv import load_dotenv
from openai import OpenAI
from source_guard import collect_dois, validate_report

load_dotenv()

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"]
)

MODEL = os.environ["LLM_MODEL"]


trusted_dois = set()



def print_checked_report(report):
    report = (report or "").strip()

    print("\n[调试] 模型正文长度：", len(report))
    print("[调试] 本轮 DOI 数量：", len(trusted_dois))

    if not report:
        print("\n[错误] 模型没有返回可见正文")
        return

    ok, reason = validate_report(
        report,
        trusted_dois
    )

    print("\n[来源校验]", reason)

    if ok:
        print("\n[SignalZero 已通过来源一致性校验的报告]")
        print(report)

    else:
        print("\n[SignalZero 未核验草稿]")
        print("⚠️ 来源校验未通过，以下内容仅供检查。")
        print("不能将其中的引用或结论视为已经核实。")
        print("\n" + report)


# Python 实际执行的查询工具
def search_publications(query):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("搜索关键词不能为空")
    # 降低请求频率，避免连续搜索触发限流
    time.sleep(2)
    response = requests.get(
        "https://api.crossref.org/works",
        params={
            "query.bibliographic": query,
            "rows": 3
        },
        headers={"User-Agent": "SignalZero/0.1 (learning project)"},
        timeout=20
    )
    response.raise_for_status()

    items = response.json()["message"]["items"]

    results = []
    for item in items:
        date_parts = item.get("published", {}).get("date-parts", [])
        date = "-".join(map(str, date_parts[0])) if date_parts else "未知"

        results.append({
            "title": item.get("title", ["未知标题"])[0],
            "doi": item.get("DOI", ""),
            "published_date": date,
            "url": item.get("URL", "")
        })

    return {"source": "Crossref", "results": results}

    trusted_dois.update(collect_dois(result))

# 告诉 Qwen 它可以使用什么工具
tools = [{
    "type": "function",
    "function": {
        "name": "search_publications",
        "description": "搜索真实学术出版记录，返回标题、DOI、出版日期和链接",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用于检索论文的关键词，优先使用英文"
                }
            },
            "required": ["query"]
        }
    }
}]

user_query = input(
    "请输入想研究的话题或需要核实的信息："
).strip()

if not user_query:
    raise SystemExit("输入不能为空，请重新运行程序。")

messages = [
    {
        "role": "system",
        "content": (
            "你是学术信息溯源助手。需要查询论文时使用工具。"
            "不能编造论文或把搜索结果当成研究结论。"
            "每条推荐的论文都必须附上本次工具返回的DOI。"
            "不得自行编造DOI或论文来源。"
            "如果工具没有提供DOI，应明确说明来源无法核实。"
            "最终请用中文生成研究总结。"
        )
    },
    {
        "role": "user",
        "content":user_query
    }
]

# 第一次请求：让模型决定是否调用工具
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message

if not message.tool_calls:
    print("本次模型没有请求工具调用：")
    print(message.content)
else:
    messages.append({
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            call.model_dump(exclude_none=True)
            for call in message.tool_calls
        ]
    })

    for call in message.tool_calls:
        print("\n[模型请求工具]", call.function.name)
        print("[模型生成参数]", call.function.arguments)

        if call.function.name != "search_publications":
            raise ValueError("不允许执行未知工具")

        arguments = json.loads(call.function.arguments)
        query = arguments.get("query")
        
        try:
            result = search_publications(query)

        except requests.exceptions.RequestException as exc:
            if (
                isinstance(exc, requests.exceptions.HTTPError)
                and exc.response is not None
                and exc.response.status_code == 429
            ):
                error_message = "Crossref 请求频率受限（429），请稍后再试"
            else:
                error_message = f"Crossref 请求失败：{type(exc).__name__}"

            print("[工具请求失败]", error_message)

            result = {
                "source": "Crossref",
                "results": [],
                "error": error_message
            }

        # 把本轮成功检索到的 DOI 保存下来
        trusted_dois.update(collect_dois(result))


        print("\n[Python 查询 Crossref 的实际结果]")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })


    
# 继续处理模型后续的工具调用
MAX_ROUNDS = 3

for round_no in range(MAX_ROUNDS):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=1000,
        extra_body={"enable_thinking": False}
    )

    choice = response.choices[0]
    message = choice.message

    print(f"\n[第 {round_no + 1} 轮]")
    print("结束原因：", choice.finish_reason)

    # 没有新的工具请求，说明可以输出回答
    if not message.tool_calls:
        print("\n[SignalZero 最终回答]")
        print_checked_report(message.content)
        break

    # 保存模型提出的工具请求
    messages.append({
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            call.model_dump(exclude_none=True)
            for call in message.tool_calls
        ]
    })

    # 执行这一轮的所有工具
    for call in message.tool_calls:
        name = call.function.name
        print("\n[继续调用工具]", name)

        if name != "search_publications":
            result = {"error": "不允许调用未知工具"}
        else:
            try:
                arguments = json.loads(call.function.arguments)
                query = arguments.get("query")

                if not isinstance(query, str) or len(query) > 200:
                    raise ValueError("无效搜索参数")

                result = search_publications(query)

            except Exception as exc:
                result = {"error": str(exc)}

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
        trusted_dois.update(collect_dois(result))

# 达到轮数上限时，停止检索并尝试生成摘要
else:
    print("\n[达到工具调用轮数上限]")

    final = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="none",
        max_tokens=1000,
        extra_body={"enable_thinking": False}
    )

    print("\n[SignalZero 最终回答]")
    print_checked_report(final.choices[0].message.content)
