"""
Multi-language detection and keyword mapping for urban risk signals.

Supports Chinese (zh) and English (en) text classification
using regex-based language detection and localized keyword rules.
"""
import re
from typing import Tuple, List
from backend.models import RiskCategory


def detect_language(text: str) -> str:
    """Detect language of input text. Returns 'zh' or 'en'."""
    cjk_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    total = max(len(text.strip()), 1)
    if cjk_count / total > 0.15:
        return "zh"
    return "en"


# Chinese keyword rules for each risk category
ZH_CATEGORY_KEYWORDS = {
    RiskCategory.crime: [
        "抢劫", "盗窃", "偷窃", "暴力", "袭击", "谋杀",
        "毒品", "破坏", "扒窃", "帮派", "家暴", "犯罪",
        "斗殴", "持刀", "持枪", "绑架", "勒索",
    ],
    RiskCategory.traffic: [
        "交通", "事故", "碰撞", "拥堵", "堵车", "封路",
        "地铁", "公交", "高速", "追尾", "闯红灯",
        "信号灯", "故障", "延误", "停运",
    ],
    RiskCategory.fraud: [
        "诈骗", "欺诈", "钓鱼", "假冒", "身份盗窃",
        "传销", "庞氏骗局", "冒充", "虚假投资",
        "电信诈骗", "网络诈骗", "骗局",
    ],
    RiskCategory.infrastructure: [
        "坍塌", "裂缝", "天坑", "洪水", "停电",
        "水管爆裂", "燃气泄漏", "路面塌陷", "桥梁",
        "电梯", "路灯", "断电", "管道破裂", "积水",
    ],
}


def match_zh_category(text: str) -> Tuple[RiskCategory, List[str]]:
    """Match Chinese text against keyword rules."""
    best_cat = RiskCategory.infrastructure
    best_score = 0
    matched_kw: List[str] = []

    for cat, keywords in ZH_CATEGORY_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in text]
        if len(hits) > best_score:
            best_score = len(hits)
            best_cat = cat
            matched_kw = hits

    return best_cat, matched_kw[:5]
