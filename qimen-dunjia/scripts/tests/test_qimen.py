#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲排盘引擎回归测试
据源：《御定奇门宝鉴》《奇门遁甲秘笈大全》《烟波钓叟歌》
运行：python3 tests/test_qimen.py 或 pytest tests/
"""
import os
import sys
# 添加三式共享库路径
# 定位共享历法库 sanzhi：兼容部署布局(shared_assets/sanzhi)与仓库布局(_shared)
_d = os.path.dirname(os.path.abspath(__file__))
while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
       and not os.path.isdir(os.path.join(_d, "_shared"))
       and os.path.dirname(_d) != _d):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
                else os.path.join(_d, "_shared"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from qimen import QimenChart


def test_dipan_nine_gan():
    """地盘必须完整分布九干（含中五寄坤二）"""
    c = QimenChart(2026, 8, 27, 16)
    gans = [d["dipan"] for d in c.chart.values() if len(d.get("dipan", "")) == 1]
    assert len(set(gans)) == 9, f"地盘应有9干，实际 {len(set(gans))}: {set(gans)}"
    print("✅ 地盘九干完整")


def test_tianpan_nine_gan():
    """天盘必须完整分布九干"""
    c = QimenChart(2026, 8, 27, 16)
    gans = [d["tianpan"] for d in c.chart.values() if len(d.get("tianpan", "")) == 1]
    assert len(set(gans)) == 9, f"天盘应有9干，实际 {len(set(gans))}: {set(gans)}"
    print("✅ 天盘九干完整")


def test_zhongwu_jingkun():
    """中五宫干寄坤二：坤二宫应以 dipan_ji 承载中五地盘干

    注：旧版断言的 dipan_note="(寄坤二)" 只是字符串标注、并不生效，
    真实寄宫由 _make_renpan 写入坤二宫的 dipan_ji（见 test_qimen_jigong.py）。
    """
    c = QimenChart(2026, 8, 27, 16)
    d5 = c.chart[5]["dipan"]
    assert c.chart[2].get("dipan_ji") == d5, (
        f"坤二宫应寄中五千{d5}，实际{c.chart[2].get('dipan_ji')}"
    )
    print("✅ 中五宫干寄坤二")


def test_shichen_hours():
    """时辰测试：子时23点、午时11点"""
    c1 = QimenChart(2026, 8, 27, 23)
    c2 = QimenChart(2026, 8, 27, 11)
    assert c1.ganzhi_shichen[1] == "子", f"23点应子时，实际{c1.ganzhi_shichen[1]}"
    assert c2.ganzhi_shichen[1] == "午", f"11点应午时，实际{c2.ganzhi_shichen[1]}"
    print("✅ 时辰边界正确")


def test_xun_shou():
    """旬首判断：时家奇门按【时柱】定旬（己巳时 → 甲子旬/戊）

    注：旧版按日柱取（己丑日→甲申旬/庚），是整盘错位的根因，已修正。
    """
    c = QimenChart(2026, 1, 15, 10)  # 己巳时
    assert c.ganzhi_time == "己巳"
    assert c.xun_shou == "甲子", f"己巳时应甲子旬，实际{c.xun_shou}"
    assert c.xun_yi == "戊", f"甲子旬首仪应戊，实际{c.xun_yi}"
    print("✅ 旬首判断正确（按时柱）")


def test_yang_yin_dun():
    """阴阳遁判断：冬至后阳遁，夏至后阴遁"""
    c_yang = QimenChart(2026, 1, 15, 10)
    c_yin = QimenChart(2026, 7, 15, 10)
    assert c_yang.is_yang_dun, "冬至后应为阳遁"
    assert not c_yin.is_yang_dun, "夏至后应为阴遁"
    print("✅ 阴阳遁判断正确")


def test_geju_db():
    """格局库加载：JSON存在则加载，否则回退"""
    import json
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "geju_db.json")
    if os.path.exists(db_path):
        data = json.load(open(db_path, encoding="utf-8"))
        assert len(data["geju"]) >= 60, f"格局库至少60条，实际{len(data['geju'])}"
    print("✅ 格局库加载正常")


def test_weathe_analysis():
    """天气分析不崩溃"""
    c = QimenChart(2026, 8, 27, 16)
    assert c.weather is not None
    print("✅ 天气分析正常")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 奇门排盘 {len(tests)} 项测试全部通过")


if __name__ == "__main__":
    run_all()