
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

API_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def search_recent_ai_papers():
    params = {
        "search_query": "cat:cs.AI AND all:agent",
        "start": 0,
        "max_results": 30,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=30
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    papers = []

    for entry in root.findall("atom:entry", NS):
        published_text = entry.findtext("atom:published", namespaces=NS)
        published = datetime.fromisoformat(
            published_text.replace("Z", "+00:00")
        )

        if published < cutoff:
            continue

        title = entry.findtext("atom:title", namespaces=NS)
        url = entry.findtext("atom:id", namespaces=NS)
        summary = entry.findtext("atom:summary", namespaces=NS)

        papers.append({
            "title": " ".join(title.split()),
            "published": published.date().isoformat(),
            "url": url,
            "summary": " ".join(summary.split())
        })

    return papers[:5]


if __name__ == "__main__":
    try:
        papers = search_recent_ai_papers()
        print(f"找到 {len(papers)} 篇最近7天的AI Agent相关论文")

        for index, paper in enumerate(papers, 1):
            print(f"\n{index}. {paper['title']}")
            print("发布日期：", paper["published"])
            print("原始链接：", paper["url"])
            print("摘要：", paper["summary"][:250], "...")

    except (requests.RequestException, ET.ParseError, ValueError) as exc:
        print("arXiv 查询或解析失败：", exc)
