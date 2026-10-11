#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传统天气占断规则（奇门遁甲/大六壬共用）
据源：《御定奇门宝鉴》《烟波钓叟歌》《六壬大全》《毕法赋》
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class WeatherTrend(Enum):
    """天气趋势"""
    SUNNY = "晴"
    CLOUDY = "阴"
    RAIN = "雨"
    SNOW = "雪"
    WIND = "风"
    FOG = "雾"
    THUNDER = "雷"
    HAIL = "雹"


@dataclass
class TraditionalWeather:
    """传统天气占断结果"""
    trend: WeatherTrend          # 主趋势
    details: List[str]           # 详细描述
    confidence: float            # 置信度 0-1
    source_rules: List[str]      # 依据规则

    def to_dict(self) -> dict:
        """转为可 JSON 序列化的字典"""
        return {
            "trend": self.trend.value,
            "details": self.details,
            "confidence": self.confidence,
            "source_rules": self.source_rules
        }


# ============================================================
# 奇门遁甲天气占断规则
# ============================================================
#
# ⚠️ 旧实现（QIMEN_STAR_WEATHER/QIMEN_DOOR_WEATHER/QIMEN_GOD_WEATHER 三表
#    "逐星逐门逐神无条件加分"）已废弃并删除。其缺陷：遍历全盘时每个九星、
#    每道八门、每位八神都必然出现一次，等于把固定权重全加一遍，
#    结果与具体盘面无关——实测任何时刻均输出"晴"且置信度恒为 1.0。
#    现改为按典籍条件判定（见 analyze_qimen_weather）。
#
# 典籍口径（多来源一致，参《奇门遁甲秘笈大全》系占天时条文）：
#   九星定天时，兼看三奇六仪、八门、八神及其落宫。
#   天蓬=水神、天柱=雨师、天辅=风伯、天英=火神(晴)、天冲=雷公、螣蛇=电母。
#   占雨：天柱/天蓬【乘壬癸】游于一、三、六、七宫主雨（壬大雨、癸小雨）；
#         临坤二宫主密云不雨；不乘壬癸则无雨。
#   占雷：天冲乘壬癸临震三宫（龙登雷门）；伤门临乾巽；临螣蛇主闪电。
#   占风：天辅落宫定风向。
#   占雪：天心/天柱乘壬癸游乾、兑二宫（限寒季）。
#   反吟主速、伏吟主迟。

# 主雨之宫（坎一、震三、乾六、兑七）
QIMEN_RAIN_PALACES = frozenset({1, 3, 6, 7})
# 主雪之宫（乾六、兑七）
QIMEN_SNOW_PALACES = frozenset({6, 7})
# 寒季（论雪之节气）
QIMEN_COLD_JIEQI = frozenset({"立冬", "小雪", "大雪", "冬至", "小寒", "大寒"})
# 八方（用于天辅定风向）；含中五（飞盘九星实落九宫，星可落中五）
QIMEN_PALACE_DIR = {1: "北", 2: "西南", 3: "东", 4: "东南", 5: "中",
                    6: "西北", 7: "西", 8: "东北", 9: "南"}
QIMEN_PALACE_NAME = {1: "坎一", 2: "坤二", 3: "震三", 4: "巽四", 5: "中五",
                     6: "乾六", 7: "兑七", 8: "艮八", 9: "离九"}


def analyze_qimen_weather(chart: Dict, jieqi: str) -> TraditionalWeather:
    """奇门遁甲天气占断（按典籍条件判定，非全盘加权求和）

    仅在典籍所述条件成立时计分；条件不成立即不计。
    无任何条件成立时返回置信度 0，不得伪装成"晴"。
    """
    def _p(key):
        return int(key)

    def find(star=None, door=None, shen=None):
        out = []
        for p, i in chart.items():
            if star and i.get("star") != star:
                continue
            if door and i.get("men") != door:
                continue
            if shen and i.get("shen") != shen:
                continue
            out.append((_p(p), i))
        return out

    scores = {w: 0.0 for w in WeatherTrend}
    rules = []
    rain_hit = False

    # ---- 占雨：天柱(雨师)/天蓬(水神) 乘壬癸 ----
    for star in ("天蓬", "天柱"):
        for p, i in find(star=star):
            gan = i.get("tianpan", "")
            if gan not in ("壬", "癸"):
                rules.append(f"{star}不乘壬癸（乘{gan or '—'}）：不主雨")
                continue
            if p == 2:
                scores[WeatherTrend.CLOUDY] += 2.0
                rules.append(f"{star}乘{gan}临坤二宫：密云不雨")
                continue
            if p in QIMEN_RAIN_PALACES:
                rain_hit = True
                big = gan == "壬"
                scores[WeatherTrend.RAIN] += 3.0 if big else 2.0
                rules.append(f"{star}乘{gan}临{QIMEN_PALACE_NAME[p]}宫：主{'大' if big else '小'}雨")
                if p == 3:
                    scores[WeatherTrend.THUNDER] += 2.0
                    rules.append(f"{star}乘{gan}临震三宫为龙登雷门：主雷阵雨")
                if i.get("men") == "伤门":
                    scores[WeatherTrend.THUNDER] += 2.0
                    rules.append(f"{star}临伤门：主雷阵雨")
                if i.get("shen") == "腾蛇":
                    scores[WeatherTrend.THUNDER] += 1.0
                    rules.append(f"{star}临螣蛇（电母）：主闪电")

    # ---- 占雷：天冲(雷公) ----
    for p, i in find(star="天冲"):
        if i.get("tianpan", "") in ("壬", "癸") and p == 3:
            scores[WeatherTrend.THUNDER] += 2.5
            rules.append("天冲乘壬癸临震三宫：主雷")
    for p, i in find(door="伤门"):
        if p in (6, 4):
            scores[WeatherTrend.THUNDER] += 1.5
            rules.append(f"伤门临{QIMEN_PALACE_NAME[p]}宫：主雷")

    # ---- 占风：天辅(风伯)落宫定风向 ----
    for p, i in find(star="天辅"):
        d = QIMEN_PALACE_DIR.get(p, "")
        scores[WeatherTrend.WIND] += 1.0
        rules.append(f"天辅（风伯）临{QIMEN_PALACE_NAME[p]}宫：主{d}风")
        if i.get("shen") in ("腾蛇", "玄武"):
            rules.append("天辅乘螣蛇/玄武：风力时大时小")
        tg, dg = i.get("tianpan", ""), i.get("dipan", "")
        if (tg, dg) in (("辛", "乙"), ("庚", "辛")):
            scores[WeatherTrend.WIND] += 2.0
            rules.append(f"天辅逢{tg}加{dg}凶格：主大风")

    # ---- 占晴：天英(火神)，以"无雨象"为前提 ----
    ying = find(star="天英")
    if ying and not rain_hit:
        scores[WeatherTrend.SUNNY] += 1.5
        rules.append("天英（火神）在盘且天蓬/天柱不乘壬癸：主晴")

    # ---- 占雪：天心/天柱乘壬癸临乾兑（限寒季） ----
    if jieqi in QIMEN_COLD_JIEQI:
        for star in ("天心", "天柱"):
            for p, i in find(star=star):
                gan = i.get("tianpan", "")
                if gan in ("壬", "癸") and p in QIMEN_SNOW_PALACES:
                    scores[WeatherTrend.SNOW] += 3.0
                    rules.append(f"{star}乘{gan}临{QIMEN_PALACE_NAME[p]}宫（寒季）：主雪")
    else:
        rules.append(f"节气{jieqi}非寒季：不论雪")

    best = max(scores.values()) if scores else 0.0
    if best <= 0:
        return TraditionalWeather(
            trend=WeatherTrend.SUNNY,
            details=["无显著天气信号：九星与壬癸/丙丁未成占雨占风之象"],
            confidence=0.0,
            source_rules=rules,
        )
    trend = max(scores.items(), key=lambda x: x[1])[0]
    confidence = min(best / 3.0, 1.0)
    return TraditionalWeather(
        trend=trend,
        details=[f"主趋势:{trend.value} 规则强度:{best:.1f} 置信度:{confidence:.2f}"],
        confidence=confidence,
        source_rules=rules,
    )


# ============================================================
# 大六壬天气占断规则
# ============================================================

# 十二将主天气
LIUREN_GOD_WEATHER = {
    "贵人": {"主": WeatherTrend.SUNNY, "描述": "主晴、贵"},
    "腾蛇": {"主": WeatherTrend.CLOUDY, "描述": "主阴、雾、怪"},
    "朱雀": {"主": WeatherTrend.SUNNY, "描述": "主晴、热、文书"},
    "六合": {"主": WeatherTrend.SUNNY, "描述": "主晴、和、雨止"},
    "勾陈": {"主": WeatherTrend.CLOUDY, "描述": "主阴、土、田"},
    "青龙": {"主": WeatherTrend.RAIN, "描述": "主雨、青、喜"},
    "天空": {"主": WeatherTrend.CLOUDY, "描述": "主阴、虚、晴"},
    "白虎": {"主": WeatherTrend.WIND, "描述": "主风、寒、白"},
    "太常": {"主": WeatherTrend.SUNNY, "描述": "主晴、文、酒"},
    "玄武": {"主": WeatherTrend.RAIN, "描述": "主雨、阴、盗"},
    "太阴": {"主": WeatherTrend.RAIN, "描述": "主雨、阴、雾"},
    "天后": {"主": WeatherTrend.CLOUDY, "描述": "主阴、云、雨"},
}

# 三传生克主天气
TRANSMISSION_WEATHER = {
    "初传生日": {"主": WeatherTrend.SUNNY, "描述": "外助晴"},
    "初传克日": {"主": WeatherTrend.RAIN, "描述": "外来雨"},
    "日生初传": {"主": WeatherTrend.CLOUDY, "描述": "内耗阴"},
    "日克初传": {"主": WeatherTrend.SUNNY, "描述": "自制晴"},
    "中传生日": {"主": WeatherTrend.SUNNY, "描述": "中助晴"},
    "中传克日": {"主": WeatherTrend.RAIN, "描述": "中阻雨"},
    "末传生日": {"主": WeatherTrend.SUNNY, "描述": "终得晴"},
    "末传克日": {"主": WeatherTrend.RAIN, "描述": "终不利雨"},
}

# 神煞主天气
SHENSHA_WEATHER = {
    "驿马": {"主": WeatherTrend.WIND, "描述": "主风、动"},
    "桃花": {"主": WeatherTrend.RAIN, "描述": "主雨、湿"},
    "文昌": {"主": WeatherTrend.SUNNY, "描述": "主晴、明"},
    "华盖": {"主": WeatherTrend.CLOUDY, "描述": "主阴、沉"},
    "劫煞": {"主": WeatherTrend.WIND, "描述": "主风、劫"},
    "灾煞": {"主": WeatherTrend.THUNDER, "描述": "主雷、灾"},
    "岁破": {"主": WeatherTrend.WIND, "描述": "主风、破"},
    "天乙贵人": {"主": WeatherTrend.SUNNY, "描述": "主晴、贵"},
}


def analyze_liuren_weather(si_ke: List, san_chuan: Dict, tian_jiang: List,
                          shen_sha: Dict, jieqi: str) -> TraditionalWeather:
    """大六壬天气占断（按条件判定，非全盘加权求和）

    ⚠️ 旧实现与奇门同病：把十二天将、全部神煞无条件各加一遍，
    再加一个硬编码的"三传占位 +0.1 雨"，故任何课都输出"晴"、置信度恒 1.0。
    现改为只计"天将临三传"与"神煞落三传"——参本 skill
    references/tian-jiang.md"天将临三传"及通行六壬占天时口诀。
    """
    scores = {w: 0.0 for w in WeatherTrend}
    rules = []

    chuan = {k: v for k, v in
             (("初传", san_chuan.get("chu", "")),
              ("中传", san_chuan.get("zhong", "")),
              ("末传", san_chuan.get("mo", ""))) if v}
    chuan_zhis = set(chuan.values())

    # ---- 天将临三传（只计落在三传上的天将） ----
    hit_gods = []
    for t in tian_jiang:
        jiang, zhi = t.get("jiang", ""), t.get("zhi", "")
        if zhi not in chuan_zhis:
            continue
        where = [k for k, v in chuan.items() if v == zhi]
        if jiang in LIUREN_GOD_WEATHER:
            rule = LIUREN_GOD_WEATHER[jiang]
            scores[rule["主"]] += 2.0
            hit_gods.append(jiang)
            rules.append(f"{jiang}临{'/'.join(where)}({zhi})：{rule['描述']}")
    if not hit_gods:
        rules.append("三传未乘天将：无天将之象可凭")

    # ---- 神煞落三传（只计落于三传的神煞） ----
    hit_ss = []
    for name, pos in shen_sha.items():
        if pos in chuan_zhis and name in SHENSHA_WEATHER:
            rule = SHENSHA_WEATHER[name]
            scores[rule["主"]] += 1.5
            hit_ss.append(name)
            rules.append(f"神煞{name}临三传({pos})：{rule['描述']}")
    if not hit_ss:
        rules.append("神煞未落三传：不作凭据")

    # ---- 日支上神之天将（取日支所乘者） ----
    ri_zhi = si_ke[2]["di"] if len(si_ke) > 2 else ""
    if ri_zhi:
        for t in tian_jiang:
            if t.get("zhi") == ri_zhi and t.get("jiang") in LIUREN_GOD_WEATHER:
                rule = LIUREN_GOD_WEATHER[t["jiang"]]
                scores[rule["主"]] += 1.0
                rules.append(f"日支{ri_zhi}乘{t['jiang']}：{rule['描述']}")

    best = max(scores.values()) if scores else 0.0
    if best <= 0:
        return TraditionalWeather(
            trend=WeatherTrend.CLOUDY,
            details=["三传未乘天将、神煞亦未落三传：无显著天气信号"],
            confidence=0.0,
            source_rules=rules,
        )
    trend = max(scores.items(), key=lambda x: x[1])[0]
    confidence = min(best / 3.0, 1.0)
    return TraditionalWeather(
        trend=trend,
        details=[f"主趋势:{trend.value} 规则强度:{best:.1f} 置信度:{confidence:.2f}"],
        confidence=confidence,
        source_rules=rules,
    )


# ============================================================
# 统一接口
# ============================================================

def analyze_weather(system: str, chart_data: Dict, **kwargs) -> TraditionalWeather:
    """
    统一天气分析接口
    system: "qimen" 或 "liuren"
    chart_data: 排盘数据
    kwargs: 额外参数 (jieqi, si_ke, san_chuan, tian_jiang, shen_sha 等)
    """
    if system == "qimen":
        return analyze_qimen_weather(chart_data.get("chart", {}), kwargs.get("jieqi", ""))
    elif system == "liuren":
        return analyze_liuren_weather(
            kwargs.get("si_ke", []), 
            kwargs.get("san_chuan", {}),
            kwargs.get("tian_jiang", []),
            kwargs.get("shen_sha", {}),
            kwargs.get("jieqi", "")
        )
    else:
        return TraditionalWeather(
            trend=WeatherTrend.SUNNY,
            details=["未知系统"],
            confidence=0.0,
            source_rules=[]
        )


if __name__ == "__main__":
    # 简单测试
    test_chart = {
        1: {"star": "天蓬", "men": "休门", "shen": "值符"},
        2: {"star": "天芮", "men": "生门", "shen": "腾蛇"},
        3: {"star": "天冲", "men": "伤门", "shen": "太阴"},
    }
    result = analyze_qimen_weather(test_chart, "谷雨")
    print(f"趋势: {result.trend.value}")
    print(f"置信度: {result.confidence}")
    print(f"规则: {result.source_rules}")