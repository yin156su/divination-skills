"""
五行系统模块
据源：《尚书·洪范》《管子·水地》《春秋繁露》《五行大义》
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass

# ============================================================
# 五行基础常量
# ============================================================

WOOD = "木"
FIRE = "火"
EARTH = "土"
METAL = "金"
WATER = "水"

FIVE_ELEMENTS = [WOOD, FIRE, EARTH, METAL, WATER]

# 统一的干支五行映射（供 ganzhi/dizhi 复用）
ELEMENT_MAP = {
    # 天干
    "甲": WOOD, "乙": WOOD, "丙": FIRE, "丁": FIRE, "戊": EARTH,
    "己": EARTH, "庚": METAL, "辛": METAL, "壬": WATER, "癸": WATER,
    # 地支
    "子": WATER, "丑": EARTH, "寅": WOOD, "卯": WOOD, "辰": EARTH,
    "巳": FIRE, "午": FIRE, "未": EARTH, "申": METAL, "酉": METAL,
    "戌": EARTH, "亥": WATER,
}

# 生克制化关系表（主动方视角）
SHENG_KE: Dict[str, Dict[str, str]] = {
    WOOD:  {"生": FIRE,  "克": EARTH, "泄": WATER,  "被克": METAL, "比和": WOOD},
    FIRE:  {"生": EARTH, "克": METAL, "泄": WOOD,   "被克": WATER, "比和": FIRE},
    EARTH: {"生": METAL, "克": WATER, "泄": FIRE,   "被克": WOOD,  "比和": EARTH},
    METAL: {"生": WATER, "克": WOOD,  "泄": EARTH,  "被克": FIRE,  "比和": METAL},
    WATER: {"生": WOOD,  "克": FIRE,  "泄": METAL,  "被克": EARTH, "比和": WATER},
}

# 关系类型常量
RELATION_SHENG = "生"
RELATION_KE = "克"
RELATION_XIE = "泄"
RELATION_BEI_KE = "被克"
RELATION_BI_HE = "比和"
RELATION_WU_GUAN = "无关"

RELATION_TYPES = [
    RELATION_SHENG, RELATION_KE, RELATION_XIE,
    RELATION_BEI_KE, RELATION_BI_HE, RELATION_WU_GUAN,
]


# ============================================================
# 核心函数
# ============================================================

def get_relation(elem1: str, elem2: str) -> str:
    """
    获取 elem1 对 elem2 的五行关系
    返回: "生" | "克" | "泄" | "被克" | "比和" | "无关"
    """
    if elem1 == elem2:
        return RELATION_BI_HE
    rels = SHENG_KE.get(elem1, {})
    for k, v in rels.items():
        if v == elem2:
            return k
    return RELATION_WU_GUAN


def get_wangxiang(elem: str, month_branch: str, day_branch: str = "") -> str:
    """
    计算五行旺相休囚（简化版：仅按月令）
    返回: "旺" | "相" | "休" | "囚" | "死"
    实际应用中需结合年月日时、藏干等综合判断
    """
    # 月令旺相表（以月支为准）
    wang_month = {WOOD: "寅卯", FIRE: "巳午", EARTH: "辰戌丑未", METAL: "申酉", WATER: "亥子"}
    xiang_month = {WOOD: "亥子", FIRE: "寅卯", EARTH: "巳午", METAL: "巳午", WATER: "申酉"}
    xiu_month = {WOOD: "申酉", FIRE: "亥子", EARTH: "寅卯", METAL: "亥子", WATER: "巳午"}
    qiu_month = {WOOD: "巳午", FIRE: "申酉", EARTH: "亥子", METAL: "寅卯", WATER: "寅卯"}
    si_month = {WOOD: "辰戌丑未", FIRE: "辰戌丑未", EARTH: "申酉", METAL: "辰戌丑未", WATER: "辰戌丑未"}

    if month_branch in wang_month.get(elem, ""):
        return "旺"
    if month_branch in xiang_month.get(elem, ""):
        return "相"
    if month_branch in xiu_month.get(elem, ""):
        return "休"
    if month_branch in qiu_month.get(elem, ""):
        return "囚"
    if month_branch in si_month.get(elem, ""):
        return "死"
    return "平"


# ============================================================
# 纳音五行（六十甲子纳音）
# ============================================================

NAYIN_MAP: Dict[str, str] = {
    # 甲子旬
    "甲子": "海中金", "乙丑": "海中金", "丙寅": "炉中火", "丁卯": "炉中火",
    "戊辰": "大林木", "己巳": "大林木", "庚午": "路旁土", "辛未": "路旁土",
    "壬申": "剑锋金", "癸酉": "剑锋金",
    # 甲戌旬
    "甲戌": "山头火", "乙亥": "山头火", "丙子": "涧下水", "丁丑": "涧下水",
    "戊寅": "城头土", "己卯": "城头土", "庚辰": "白蜡金", "辛巳": "白蜡金",
    "壬午": "杨柳木", "癸未": "杨柳木",
    # 甲申旬
    "甲申": "泉中水", "乙酉": "泉中水", "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹雳火", "己丑": "霹雳火", "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "长流水", "癸巳": "长流水",
    # 甲午旬
    "甲午": "砂中金", "乙未": "砂中金", "丙申": "山下火", "丁酉": "山下火",
    "戊戌": "平地木", "己亥": "平地木", "庚子": "壁上土", "辛丑": "壁上土",
    "壬寅": "金箔金", "癸卯": "金箔金",
    # 甲辰旬
    "甲辰": "覆灯火", "乙巳": "覆灯火", "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驿土", "己酉": "大驿土", "庚戌": "钗钏金", "辛亥": "钗钏金",
    "壬子": "桑柘木", "癸丑": "桑柘木",
    # 甲寅旬
    "甲寅": "大溪水", "乙卯": "大溪水", "丙辰": "沙中土", "丁巳": "沙中土",
    "戊午": "天上火", "己未": "天上火", "庚申": "石榴木", "辛酉": "石榴木",
    "壬戌": "大海水", "癸亥": "大海水",
}


def get_nayin(ganzhi: str) -> str:
    """获取干支的纳音五行"""
    return NAYIN_MAP.get(ganzhi, "未知")


# ============================================================
# 干支五行获取（统一接口）
# ============================================================

def get_stem_element(gan: str) -> str:
    """获取天干五行"""
    return ELEMENT_MAP.get(gan, "")


def get_branch_element(zhi: str) -> str:
    """获取地支五行"""
    return ELEMENT_MAP.get(zhi, "")


def get_ganzhi_element(gan: str, zhi: str) -> Dict[str, str]:
    """获取干支双方五行"""
    return {"gan": get_stem_element(gan), "zhi": get_branch_element(zhi)}


__all__ = [
    "WOOD", "FIRE", "EARTH", "METAL", "WATER",
    "FIVE_ELEMENTS",
    "ELEMENT_MAP", "SHENG_KE",
    "RELATION_SHENG", "RELATION_KE", "RELATION_XIE",
    "RELATION_BEI_KE", "RELATION_BI_HE", "RELATION_WU_GUAN",
    "get_relation", "get_wangxiang",
    "NAYIN_MAP", "get_nayin",
    "get_stem_element", "get_branch_element", "get_ganzhi_element",
]