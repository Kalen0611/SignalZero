
import re


def extract_arxiv_ids(text):
    return set(re.findall(
        r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?",
        text or "",
        flags=re.IGNORECASE
    ))


def validate_arxiv_report(report, paper_urls):
    allowed = extract_arxiv_ids("\n".join(paper_urls))
    cited = extract_arxiv_ids(report)

    if not cited:
        return False, "报告没有引用 arXiv 论文"

    unknown = cited - allowed

    if unknown:
        return False, f"未检索的论文编号：{sorted(unknown)}"

    return True, f"{len(cited)} 篇引用均来自本轮检索"
