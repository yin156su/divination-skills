"""
节气系统模块
据源：《后汉书·律历志》《晋书·天文志》《宋史·天文志》《协纪辨方书》
包含：二十四节气、中气、月将、阴阳遁判定、三元
"""

from typing import Dict, List, Optional, Literal
from datetime import date
from dataclasses import dataclass

# ============================================================
# 二十四节气常量
# ============================================================

JIEQI_LIST = [
    "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]

# 节气分类：节气 vs 中气（中气用于月将切换）
JIEQI_TYPE = {
    # 节气（交节）
    "立春": "节", "惊蛰": "节", "清明": "节", "立夏": "节", "芒种": "节",
    "小暑": "节", "立秋": "节", "白露": "节", "寒露": "节", "立冬": "节",
    "大雪": "节", "小寒": "节",
    # 中气（中气）
    "雨水": "中", "春分": "中", "谷雨": "中", "小满": "中", "夏至": "中",
    "大暑": "中", "处暑": "中", "秋分": "中", "霜降": "中", "小雪": "中",
    "冬至": "中", "大寒": "中",
}

# 中气 → 月将映射（太阳过宫，以中气为换将节点）
# 据《六壬大全》卷一、奇门遁甲《御定奇门宝鉴》
ZHONGQI_YUEJIANG = {
    "冬至": "丑", "大寒": "子", "雨水": "亥", "春分": "戌",
    "谷雨": "酉", "小满": "申", "夏至": "未", "大暑": "午",
    "处暑": "巳", "秋分": "辰", "霜降": "卯", "小雪": "寅",
}

# 节气序号（用于计算）
JIEQI_ORDER = {jq: i for i, jq in enumerate(JIEQI_LIST)}

# 阳遁/阴遁节气范围
# 阳遁：冬至至芒种前（冬至、小寒、大寒、立春、雨水、惊蛰、春分、清明、谷雨、立夏、小满、芒种）
# 阴遁：夏至至大雪前（夏至、小暑、大暑、立秋、处暑、白露、秋分、寒露、霜降、立冬、小雪、大雪）
YANG_DUN_JIEQI = frozenset([
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种"
])
YIN_DUN_JIEQI = frozenset([
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"
])


# ============================================================
# 节气数据结构
# ============================================================

@dataclass
class JieQiInfo:
    name: str
    type: str  # "节" or "中"
    solar_date: date  # 该年该节气的公历日期
    index: int  # 0-23


# ============================================================
# 核心函数（需配合 LunarProvider 使用）
# ============================================================

def get_current_jieqi(year: int, month: int, day: int, hour: int = 12,
                      lunar_provider=None) -> JieQiInfo:
    """
    获取指定日期的前一节气（节气/中气均可）
    需要传入 lunar_provider 实例
    """
    if lunar_provider is None:
        raise ValueError("必须提供 lunar_provider")
    
    s = lunar_provider.get_solar(year, month, day, hour)
    l = s.getLunar()
    jq_obj = l.getPrevJieQi()
    name = jq_obj.getName() if hasattr(jq_obj, "getName") else "冬至"
    jq_type = JIEQI_TYPE.get(name, "节")
    
    # 获取该节气在当年的确切日期
    table = l.getJieQiTable()
    jq = table.get(name)
    if jq:
        solar_date = date(jq.getYear(), jq.getMonth(), jq.getDay())
    else:
        solar_date = date(year, month, day)
    
    return JieQiInfo(
        name=name,
        type=jq_type,
        solar_date=solar_date,
        index=JIEQI_ORDER.get(name, 0)
    )


def get_yuejiang(year: int, month: int, day: int, hour: int = 12,
                 lunar_provider=None) -> str:
    """
    获取月将（按中气定）
    据《六壬大全》首传法、奇门《烟波钓叟歌》
    月将 = 太阳躔度宫位，以中气为换将节点
    """
    jq_info = get_current_jieqi(year, month, day, hour, lunar_provider)
    # 必须是中气才能定月将；若当前是节气，需回退到上一个中气
    if jq_info.type == "节":
        # 找上一个中气
        idx = (jq_info.index - 1) % 24
        while JIEQI_TYPE.get(JIEQI_LIST[idx]) != "中":
            idx = (idx - 1) % 24
        zhongqi_name = JIEQI_LIST[idx]
    else:
        zhongqi_name = jq_info.name
    
    return ZHONGQI_YUEJIANG.get(zhongqi_name, "亥")


def get_yang_yin_dun(jieqi_name: str) -> str:
    """根据节气名判断阴阳遁"""
    if jieqi_name in YANG_DUN_JIEQI:
        return "阳遁"
    return "阴遁"


def is_yang_dun(jieqi_name: str) -> bool:
    """是否阳遁"""
    return jieqi_name in YANG_DUN_JIEQI


def get_yuan(year: int, month: int, day: int, jieqi_name: str,
             lunar_provider=None) -> int:
    """
    三元：距节气天数 ÷ 5（0=上元, 1=中元, 2=下元）
    每元5天，三元15天
    """
    jq_info = get_current_jieqi(year, month, day, 12, lunar_provider)
    # 如果查询的节气与当前节气不同，需获取指定节气日期
    if jq_info.name != jieqi_name:
        # 简化：假设传入的是当前节气
        pass
    
    target_date = date(year, month, day)
    diff = (target_date - jq_info.solar_date).days
    return max(0, diff // 5) % 3


# ============================================================
# 三式专用局数表（拆补法，据《烟波钓叟歌》）
# ============================================================

# 阳遁九局（冬至→芒种）
YANG_JU_TABLE = {
    "冬至": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6),
    "立春": (8, 5, 2), "雨水": (9, 6, 3), "惊蛰": (1, 7, 4),
    "春分": (3, 9, 6), "清明": (4, 1, 7), "谷雨": (5, 2, 8),
    "立夏": (4, 1, 7), "小满": (5, 2, 8), "芒种": (6, 3, 9),
}

# 阴遁九局（夏至→大雪）
YIN_JU_TABLE = {
    "夏至": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4),
    "立秋": (2, 5, 8), "处暑": (1, 4, 7), "白露": (9, 3, 6),
    "秋分": (7, 1, 4), "寒露": (6, 9, 3), "霜降": (5, 8, 2),
    "立冬": (6, 9, 3), "小雪": (5, 8, 2), "大雪": (4, 7, 1),
}


def get_ju_number(jieqi_name: str, yuan: int, is_yang_dun: bool) -> int:
    """根据节气、元、阴阳遁获取局数"""
    table = YANG_JU_TABLE if is_yang_dun else YIN_JU_TABLE
    return table.get(jieqi_name, (1, 7, 4) if is_yang_dun else (9, 3, 6))[yuan]


# 兼容别名
ZHONGQI_MAP = ZHONGQI_YUEJIANG
YUEJIANG_MAP = ZHONGQI_YUEJIANG

__all__ = [
    "JIEQI_LIST", "JIEQI_TYPE", "ZHONGQI_YUEJIANG", "ZHONGQI_MAP", "YUEJIANG_MAP", "JIEQI_ORDER",
    "YANG_DUN_JIEQI", "YIN_DUN_JIEQI",
    "JieQiInfo",
    "get_current_jieqi", "get_yuejiang", "get_yang_yin_dun",
    "is_yang_dun", "get_yuan",
    "YANG_JU_TABLE", "YIN_JU_TABLE", "get_ju_number",
]