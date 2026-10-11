#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天气占断回归测试（防"假数据"复发）

历史缺陷：weather_traditional 的奇门/六壬天气分析把全盘九星、八门、八神
（六壬为十二天将、全部神煞）**无条件各加一遍**，等于常量求和：
实测任何时刻均输出"晴"、置信度恒为 1.0，与盘面无关。
现改为按典籍条件判定，本测试锁定其"确实随盘面变化"。

运行：python3 tests/test_weather.py 或 pytest tests/
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
       and not os.path.isdir(os.path.join(_d, "_shared"))
       and os.path.dirname(_d) != _d):
    _d = os.path.dirname(_d)
_SHARED = (os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
           else os.path.join(_d, "_shared"))
sys.path.insert(0, _SHARED)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from sanzhi import weather_traditional as W  # noqa: E402

CASES = ((2026, 1, 15, 12), (2026, 4, 15, 12), (2026, 7, 15, 12),
         (2026, 10, 10, 12), (2026, 8, 31, 16))


def test_qimen_weather_varies():
    """奇门天气须随时刻变化（旧实现恒为'晴'）"""
    import qimen
    results = []
    for y, m, d, h in CASES:
        c = qimen.QimenChart(y, m, d, h, pan_style="zhuanpan")
        w = c.weather
        results.append((w["trend"], round(w["confidence"], 3)))
    assert len(set(results)) > 1, f"天气结果不应恒定，实得: {results}"
    print(f"✅ 奇门天气随盘面变化: {results}")


def test_qimen_no_deprecated_tables():
    """已废的三张'无条件加分'表不得复活"""
    for name in ("QIMEN_STAR_WEATHER", "QIMEN_DOOR_WEATHER", "QIMEN_GOD_WEATHER"):
        assert not hasattr(W, name), f"{name} 应已删除（无条件加分即假数据）"
    print("✅ 旧加分表已删除")


def test_renpao_bu_cheng_renkui_no_rain():
    """天蓬/天柱不乘壬癸则不计雨——条件判定之核心"""
    chart = {
        1: {"star": "天蓬", "dipan": "戊", "tianpan": "丙"},   # 不乘壬癸
        3: {"star": "天柱", "dipan": "庚", "tianpan": "辛"},   # 不乘壬癸
        9: {"star": "天英", "dipan": "丙", "tianpan": "丁"},
    }
    w = W.analyze_qimen_weather(chart, "清明")
    assert w.trend.value != "雨", f"不乘壬癸不应主雨，实得{w.trend.value}"
    assert any("不乘壬癸" in r for r in w.source_rules), "应有'不乘壬癸'之判"
    print("✅ 不乘壬癸不主雨")


def test_cheng_renkui_in_rain_palace():
    """天蓬乘壬临坎一宫 → 主雨（典籍条件成立）"""
    chart = {
        1: {"star": "天蓬", "dipan": "戊", "tianpan": "壬", "men": "休门", "shen": "太阴"},
    }
    w = W.analyze_qimen_weather(chart, "清明")
    assert w.trend.value == "雨", f"天蓬乘壬临坎一应主雨，实得{w.trend.value}"
    assert w.confidence > 0
    print("✅ 天蓬乘壬临坎一主雨")


def test_kun2_miyun_buyu():
    """天柱乘壬临坤二宫 → 密云不雨"""
    chart = {2: {"star": "天柱", "dipan": "乙", "tianpan": "壬"}}
    w = W.analyze_qimen_weather(chart, "清明")
    assert w.trend.value != "雨", "临坤二不应主雨"
    assert any("密云不雨" in r for r in w.source_rules)
    print("✅ 临坤二密云不雨")


def test_no_signal_confidence_zero():
    """无任何条件成立时置信度须为 0，不得伪装成'晴'"""
    w = W.analyze_qimen_weather({}, "清明")
    assert w.confidence == 0.0, f"无信号时置信度应为0，实得{w.confidence}"
    print("✅ 无信号时置信度为0")


def test_snow_only_in_cold_season():
    """占雪限寒季"""
    chart = {6: {"star": "天心", "dipan": "辛", "tianpan": "壬"}}
    cold = W.analyze_qimen_weather(chart, "大雪")
    warm = W.analyze_qimen_weather(chart, "清明")
    assert cold.trend.value == "雪", f"寒季应主雪，实得{cold.trend.value}"
    assert warm.trend.value != "雪", "非寒季不应主雪"
    print("✅ 占雪限寒季")


def test_liuren_weather_varies():
    """六壬天气须随课体变化（旧实现恒为'晴'）"""
    import importlib
    import glob
    # 兼容多种部署/仓库布局：skills/da-liu-ren、_shared 同级、或根目录平铺
    cands = (
        glob.glob(os.path.join(_d, "skills", "da-liu-ren", "scripts"))
        + glob.glob(os.path.join(_d, "*", "da-liu-ren", "scripts"))
        + glob.glob(os.path.join(_d, "da-liu-ren", "scripts"))
    )
    cands = sorted(set(cands))
    assert cands, f"未找到 da-liu-ren/scripts（从 {_d} 起，布局: skills/、*/、直接平铺 均未命中）"
    if cands[0] not in sys.path:
        sys.path.insert(0, cands[0])
    liuren = importlib.import_module("liuren")
    results = []
    for y, m, d, h in CASES:
        c = liuren.LiuRenCalculator(y, m, d, h)
        w = c.weather
        results.append((w["trend"], round(w["confidence"], 3)))
    assert len(set(results)) > 1, f"六壬天气结果不应恒定，实得: {results}"
    print(f"✅ 六壬天气随课体变化: {results}")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 天气占断回归 {len(tests)} 项全部通过")


if __name__ == "__main__":
    run_all()