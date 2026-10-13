
import re

DOI_PATTERN = re.compile(
    r"10\.\d{4,9}/[^\s<>\[\](){}，。；！？、,;\"']+",
    re.IGNORECASE
)


def extract_dois(text):
    """从文本中提取并规范化 DOI。"""
    return {
        match.group(0).rstrip(".:").lower()
        for match in DOI_PATTERN.finditer(text or "")
    }


def collect_dois(result):
    """仅收集本次工具返回的 DOI。"""
    dois = set()

    for item in result.get("results", []):
        doi = item.get("doi")

        if isinstance(doi, str) and doi.strip():
            dois.add(doi.strip().lower())

    return dois


def validate_report(report, trusted_dois):
    """检查报告中的 DOI 是否都来自工具结果。"""
    cited_dois = extract_dois(report)

    if not cited_dois:
        return False, "报告没有提供可核对的 DOI"

    unknown = cited_dois - trusted_dois

    if unknown:
        return False, (
            "以下 DOI 未出现在本次工具结果中："
            + ", ".join(sorted(unknown))
        )

    return True, "所有引用的 DOI 均来自本次工具结果"
