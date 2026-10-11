"""
地支系统模块
据源：《后汉书·律历志》《三命通会》《穿杨秘诀》《神峰通考》
包含：六冲、六合、三合、三会、刑、害、藏干、正气/中气/余气
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

from .ganzhi import BRANCH_TO_IDX, EARTHLY_BRANCHES
from .wuxing import ELEMENT_MAP

# ============================================================
# 基础关系表
# ============================================================

# 六冲
LIU_CHONG = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 六合
LIU_HE = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午",
}

# 三合局（水木火金）
SAN_HE = {
    "水": ["申", "子", "辰"],
    "木": ["亥", "卯", "未"],
    "火": ["寅", "午", "戌"],
    "金": ["巳", "酉", "丑"],
}

# 三会方（东南西北）
SAN_HUI = {
    "东": ["寅", "卯", "辰"],  # 木方
    "南": ["巳", "午", "未"],  # 火方
    "西": ["申", "酉", "戌"],  # 金方
    "北": ["亥", "子", "丑"],  # 水方
}

# 刑（三刑、自刑）
XING = {
    # 恃势之刑
    "寅": "巳", "巳": "申", "申": "寅",
    # 无恩之刑
    "丑": "戌", "戌": "未", "未": "丑",
    # 自刑
    "辰": "辰", "午": "午", "酉": "酉", "亥": "亥",
    # 子卯刑（无礼之刑）
    "子": "卯", "卯": "子",
}

# 害（六害）
HAI = {
    "子": "未", "未": "子",
    "丑": "午", "午": "丑",
    "寅": "巳", "巳": "寅",
    "卯": "辰", "辰": "卯",
    "申": "亥", "亥": "申",
    "酉": "戌", "戌": "酉",
}

# 藏干表（人元、地元、天元）
ZHI_CANGGAN = {
    "子": [("癸", "正气")],
    "丑": [("己", "正气"), ("癸", "中气"), ("辛", "余气")],
    "寅": [("甲", "正气"), ("丙", "中气"), ("戊", "余气")],
    "卯": [("乙", "正气")],
    "辰": [("戊", "正气"), ("乙", "中气"), ("癸", "余气")],
    "巳": [("丙", "正气"), ("庚", "中气"), ("戊", "余气")],
    "午": [("丁", "正气"), ("己", "中气")],
    "未": [("己", "正气"), ("丁", "中气"), ("乙", "余气")],
    "申": [("庚", "正气"), ("壬", "中气"), ("戊", "余气")],
    "酉": [("辛", "正气")],
    "戌": [("戊", "正气"), ("辛", "中气"), ("丁", "余气")],
    "亥": [("壬", "正气"), ("甲", "中气")],
}

# 正气/中气/余气映射
ZHI_ZHENGQI = {k: v[0][0] for k, v in ZHI_CANGGAN.items()}
ZHI_ZHONGQI = {k: v[1][0] for k, v in ZHI_CANGGAN.items() if len(v) > 1}
ZHI_YUQI = {k: v[2][0] for k, v in ZHI_CANGGAN.items() if len(v) > 2}

# 驿马、文昌、华盖、劫煞、灾煞（按日支/年支查）
YIMA_MAP = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}

WENCHANG_MAP = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉",
    "戊": "申", "己": "酉", "庚": "寅", "辛": "卯",
    "壬": "巳", "癸": "午",
}

HUAGAI_MAP = {
    "申": "辰", "子": "辰", "辰": "辰",
    "寅": "戌", "午": "戌", "戌": "戌",
    "巳": "丑", "酉": "丑", "丑": "丑",
    "亥": "未", "卯": "未", "未": "未",
}

JIESHA_MAP = {
    "申": "巳", "子": "巳", "辰": "巳",
    "寅": "亥", "午": "亥", "戌": "亥",
    "巳": "午", "酉": "午", "丑": "午",
    "亥": "寅", "卯": "寅", "未": "寅",
}

ZAISHA_MAP = {
    "申": "午", "子": "午", "辰": "午",
    "寅": "子", "午": "子", "戌": "子",
    "巳": "申", "酉": "申", "丑": "申",
    "亥": "辰", "卯": "辰", "未": "辰",
}


# ============================================================
# 核心函数
# ============================================================

def is_liu_chong(zhi1: str, zhi2: str) -> bool:
    """判断两地支是否六冲"""
    return LIU_CHONG.get(zhi1) == zhi2


def is_liu_he(zhi1: str, zhi2: str) -> bool:
    """判断两地支是否六合"""
    return LIU_HE.get(zhi1) == zhi2


def get_he(zhi: str) -> str:
    """获取地支的六合对应支"""
    return LIU_HE.get(zhi, "")


def get_sanhe(zhi: str) -> List[str]:
    """获取地支所属的三合局列表"""
    for element, branches in SAN_HE.items():
        if zhi in branches:
            return branches.copy()
    return []


def get_san_hui(zhi: str) -> List[str]:
    """获取地支所属的三会方列表"""
    for direction, branches in SAN_HUI.items():
        if zhi in branches:
            return branches.copy()
    return []


def get_xing(zhi: str) -> str:
    """获取地支的刑对应支"""
    return XING.get(zhi, "")


def get_hai(zhi: str) -> str:
    """获取地支的害对应支"""
    return HAI.get(zhi, "")


def get_zhi_wuxing(zhi: str) -> str:
    """获取地支五行"""
    return ELEMENT_MAP.get(zhi, "")


def get_zhi_yinyang(zhi: str) -> str:
    """获取地支阴阳"""
    return "阳" if zhi in ["子", "寅", "辰", "午", "申", "戌"] else "阴"


def get_zhi_canggan(zhi: str) -> List[Tuple[str, str]]:
    """获取地支藏干列表 [(干, 气类型), ...]"""
    return ZHI_CANGGAN.get(zhi, []).copy()


def get_zhi_zhengqi(zhi: str) -> str:
    """获取地支正气"""
    return ZHI_ZHENGQI.get(zhi, "")


def get_zhi_zhongqi(zhi: str) -> str:
    """获取地支中气"""
    return ZHI_ZHONGQI.get(zhi, "")


def get_zhi_yuqi(zhi: str) -> str:
    """获取地支余气"""
    return ZHI_YUQI.get(zhi, "")


# ============================================================
# 高级查询
# ============================================================

def get_chong_sha(year_zhi: str) -> str:
    """岁破：与年支相冲"""
    return LIU_CHONG.get(year_zhi, "")


def get_relations_for_zhi(zhi: str) -> Dict[str, str]:
    """获取某地支的所有关系：冲、合、刑、害、驿马等"""
    return {
        "冲": LIU_CHONG.get(zhi, ""),
        "合": LIU_HE.get(zhi, ""),
        "刑": XING.get(zhi, ""),
        "害": HAI.get(zhi, ""),
        "驿马": YIMA_MAP.get(zhi, ""),
        "华盖": HUAGAI_MAP.get(zhi, ""),
        "劫煞": JIESHA_MAP.get(zhi, ""),
        "灾煞": ZAISHA_MAP.get(zhi, ""),
    }


__all__ = [
    "LIU_CHONG", "LIU_HE", "SAN_HE", "SAN_HUI", "XING", "HAI",
    "ZHI_CANGGAN", "ZHI_ZHENGQI", "ZHI_ZHONGQI", "ZHI_YUQI",
    "YIMA_MAP", "WENCHANG_MAP", "HUAGAI_MAP", "JIESHA_MAP", "ZAISHA_MAP",
    "is_liu_chong", "is_liu_he", "get_he", "get_sanhe", "get_san_hui",
    "get_xing", "get_hai", "get_zhi_wuxing", "get_zhi_yinyang",
    "get_zhi_canggan", "get_zhi_zhengqi", "get_zhi_zhongqi", "get_zhi_yuqi",
    "get_chong_sha", "get_relations_for_zhi",
]