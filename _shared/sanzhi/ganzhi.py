"""
干支系统模块
据源：《后汉书·律历志》《晋书·天文志》《三命通会》《子平真诠》
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# ============================================================
# 基础常量
# ============================================================

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_TO_IDX = {s: i for i, s in enumerate(HEAVENLY_STEMS)}
BRANCH_TO_IDX = {b: i for i, b in enumerate(EARTHLY_BRANCHES)}

# 六十甲子
LIUSHI_JIAZI = [HEAVENLY_STEMS[i % 10] + EARTHLY_BRANCHES[i % 12] for i in range(60)]

# 天干阴阳
YANG_STEMS = frozenset("甲丙戊庚壬")
YIN_STEMS = frozenset("乙丁己辛癸")

# 地支阴阳
YANG_BRANCHES = frozenset("子寅辰午申戌")
YIN_BRANCHES = frozenset("丑卯巳未酉亥")

# 旬首表（六甲对应的六仪）
XUN_SHOU_YI = {
    "甲子": "戊", "甲戌": "己", "甲申": "庚",
    "甲午": "辛", "甲辰": "壬", "甲寅": "癸",
}

# 旬空表
XUN_KONG = {
    "甲子": ["戌", "亥"], "甲戌": ["申", "酉"], "甲申": ["午", "未"],
    "甲午": ["辰", "巳"], "甲辰": ["寅", "卯"], "甲寅": ["子", "丑"],
}

# 日干寄宫（阳干寄禄，阴干寄禄之后一辰）
GAN_GONG = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
    "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑",
}

# 五行属性（用于干支）
STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
    "戌": "土", "亥": "水",
}


# ============================================================
# 核心函数
# ============================================================

def get_shichen(hour: int) -> str:
    """
    小时(0-23)转时辰地支
    子时：23:00-01:00，丑时：01:00-03:00...
    """
    if hour == 23 or hour < 1:
        return "子"
    return EARTHLY_BRANCHES[(hour + 1) // 2 % 12]


def get_xun_shou(day_gan: str, day_zhi: str) -> str:
    """
    旬首：干支所在旬的甲头
    例如：己丑日 -> 甲申旬
    """
    ganzhi = day_gan + day_zhi
    idx = LIUSHI_JIAZI.index(ganzhi)
    xun_idx = idx // 10 * 10
    return LIUSHI_JIAZI[xun_idx]


def get_kong_wang(day_gan: str, day_zhi: str) -> List[str]:
    """旬空：返回当日旬首对应的空亡地支列表"""
    ganzhi = day_gan + day_zhi
    idx = LIUSHI_JIAZI.index(ganzhi)
    xun_idx = idx // 10 * 10
    xun_shou = LIUSHI_JIAZI[xun_idx]
    return XUN_KONG.get(xun_shou, [])


def get_ganzhi_from_stem_branch(gan: str, zhi: str) -> str:
    """干支组合（校验合法性）"""
    if gan not in STEM_TO_IDX or zhi not in BRANCH_TO_IDX:
        raise ValueError(f"非法干支: {gan}{zhi}")
    # 检查阴阳匹配（阳干配阳支，阴干配阴支）
    gan_yang = gan in YANG_STEMS
    zhi_yang = zhi in YANG_BRANCHES
    if gan_yang != zhi_yang:
        raise ValueError(f"干支阴阳不匹配: {gan}{zhi}")
    return gan + zhi


def get_liushijiazi() -> List[str]:
    """获取六十甲子完整列表"""
    return LIUSHI_JIAZI.copy()


# ============================================================
# 农历干支获取（依赖 LunarProvider，由各 skill 实现时注入）
# ============================================================

@dataclass
class LunarGanZhi:
    """农历干支数据容器"""
    year: str      # 年柱
    month: str     # 月柱
    day: str       # 日柱
    time: str      # 时柱
    lunar_date: str  # 农历日期字符串

    @property
    def ri_gan(self) -> str:
        return self.day[0]

    @property
    def ri_zhi(self) -> str:
        return self.day[1]

    @property
    def shi_gan(self) -> str:
        return self.time[0]

    @property
    def shi_zhi(self) -> str:
        return self.time[1]

    @property
    def yue_zhi(self) -> str:
        return self.month[1]

    @property
    def nian_gan(self) -> str:
        return self.year[0]

    @property
    def nian_zhi(self) -> str:
        return self.year[1]


def get_ganzhi_year(year: int) -> str:
    """获取年柱干支（简化：仅作接口占位，实际需农历库）"""
    # 实际使用时应调用 LunarProvider
    raise NotImplementedError("需配合 LunarProvider 使用")


def get_ganzhi_month(year: int, month: int) -> str:
    """获取月柱干支（简化：仅作接口占位）"""
    raise NotImplementedError("需配合 LunarProvider 使用")


def get_ganzhi_day(year: int, month: int, day: int) -> str:
    """获取日柱干支（简化：仅作接口占位）"""
    raise NotImplementedError("需配合 LunarProvider 使用")


def get_ganzhi_time(year: int, month: int, day: int, hour: int) -> str:
    """获取时柱干支（简化：仅作接口占位）"""
    raise NotImplementedError("需配合 LunarProvider 使用")


__all__ = [
    "HEAVENLY_STEMS", "EARTHLY_BRANCHES",
    "STEM_TO_IDX", "BRANCH_TO_IDX",
    "LIUSHI_JIAZI",
    "YANG_STEMS", "YIN_STEMS",
    "YANG_BRANCHES", "YIN_BRANCHES",
    "XUN_SHOU_YI", "XUN_KONG",
    "GAN_GONG",
    "STEM_ELEMENT", "BRANCH_ELEMENT",
    "get_shichen", "get_xun_shou", "get_kong_wang",
    "get_ganzhi_from_stem_branch", "get_liushijiazi",
    "LunarGanZhi",
    "get_ganzhi_year", "get_ganzhi_month", "get_ganzhi_day", "get_ganzhi_time",
]