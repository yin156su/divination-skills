#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞盘结构回归测试（防复发）

飞盘（《奇门法窍》系）与转盘的关键差别，逐条锁定：
  A 九干/九星实落九宫（中五得干、得天禽），不得有"寄坤二"标注
  B 甲时天盘伏吟（天盘 == 地盘）
  C 非甲时：天盘为地盘按洛书序整体飞移（位次关系固定）
  D 值符落宫 = 时干宫；值符星随旬首仪（壬→天禽，本位中五）
  E 值符神落值符落宫
  F 门/星/神八宫（飞盘九宫）不重复、无空缺
  G 旬首仪落中五时，飞盘按实落取 5（不寄坤二）

运行：python3 tests/test_qimen_feipan.py 或 pytest tests/
"""
import os
import sys
from datetime import date, timedelta

_d = os.path.dirname(os.path.abspath(__file__))
while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
       and not os.path.isdir(os.path.join(_d, "_shared"))
       and os.path.dirname(_d) != _d):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
                else os.path.join(_d, "_shared"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from qimen import QimenChart, STAR_HOME, YI_TO_STAR_FEI, STAR_RING_FEI  # noqa: E402

PAL8 = [1, 2, 3, 4, 6, 7, 8, 9]
CASES = ((2026, 1, 15, 10), (2026, 2, 4, 16), (2026, 8, 31, 16), (2025, 3, 8, 0))


def _jia_hours(n=6):
    hits = []
    d0 = date(2026, 1, 1)
    from lunar_python import Solar
    for k in range(400):
        d = d0 + timedelta(days=k)
        for h in (0, 12):
            if Solar(d.year, d.month, d.day, h, 0, 0).getLunar().getTimeInGanZhi()[0] == "甲":
                hits.append((d, h))
        if len(hits) >= n:
            break
    return hits[:n]


def test_feipan_star_ring_canonical():
    """飞盘星序含中五天禽，本位一致"""
    assert STAR_RING_FEI == [STAR_HOME[p] for p in range(1, 10)]
    assert STAR_RING_FEI == ["天蓬", "天芮", "天冲", "天辅", "天禽",
                            "天心", "天柱", "天任", "天英"]
    assert YI_TO_STAR_FEI["壬"] == "天禽", "飞盘壬仪值符星应天禽（本位中五），不寄芮"
    print("✅ 飞盘星序/值符星映射正确")


def test_feipan_no_jikun2():
    """飞盘九干九星实落九宫，中五不得出现'寄坤二'标注"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="feipan")
        assert "dipan_note" not in c.chart.get(5, {}), f"{y}-{m}-{d} {h}时 中五残留寄坤二标注"
        gans = [c.chart[p].get("dipan") for p in range(1, 10)]
        assert all(gans) and len(set(gans)) == 9, f"九干应实落九宫：{gans}"
        stars = [c.chart[p].get("star") for p in range(1, 10)]
        assert all(stars) and len(set(stars)) == 9, f"九星应实落九宫：{stars}"
    print("✅ 飞盘九干/九星实落九宫，无寄坤二")


def test_feipan_jia_hour_fuyin():
    """甲时天盘须伏吟（含中五）"""
    for d, h in _jia_hours(6):
        c = QimenChart(d.year, d.month, d.day, h, pan_style="feipan")
        assert c.shi_gan == "甲"
        for p in range(1, 10):
            assert c.chart[p]["tianpan"] == c.chart[p]["dipan"], (
                f"{d} {h}时 宫{p} 天盘{c.chart[p]['tianpan']}≠地盘{c.chart[p]['dipan']}"
            )
    print("✅ 飞盘甲时伏吟")


def test_feipan_tianpan_is_shift():
    """非甲时：天盘应为地盘按洛书序整体飞移（位次关系守恒）"""
    checked = 0
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="feipan")
        if c.shi_gan == "甲":
            continue
        di = {p: c.chart[p]["dipan"] for p in range(1, 10)}
        tp = {p: c.chart[p]["tianpan"] for p in range(1, 10)}
        assert set(tp.values()) == set(di.values()), "天盘干集合应等于地盘干集合"
        # 找飞移步数 S：对每宫 p，天盘干 = 地盘自 p 回退 S 步之干
        ok_S = None
        for S in range(9):
            if all(tp[p] == di[c._fly9(p)[-S % 9]] for p in range(1, 10)):
                ok_S = S
                break
        assert ok_S is not None, f"{y}-{m}-{d} {h}时 天盘不是地盘的洛书整体飞移"
        checked += 1
    assert checked > 0
    print(f"✅ 飞盘天盘为整体飞移（验 {checked} 盘）")


def test_feipan_zhifu_and_shen():
    """值符落宫=时干宫；值符星随旬首仪；值符神落该宫"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="feipan")
        pz = c._zhifu_palace()
        tg_pal = [p for p in range(1, 10) if c.chart[p]["dipan"] == c.shi_gan][0]
        assert pz == tg_pal, f"{y}-{m}-{d} {h}时 值符落宫应=时干宫{tg_pal}，实得{pz}"
        assert c.chart[pz]["star"] == YI_TO_STAR_FEI[c.xun_yi], (
            f"仪{c.xun_yi} 值符宫{pz}星应{YI_TO_STAR_FEI[c.xun_yi]}，实得{c.chart[pz]['star']}"
        )
        assert c.chart[pz]["shen"] == "值符", "值符神应落值符落宫"
    print("✅ 飞盘值符落宫/星/神一致")


def test_feipan_no_duplicate():
    """飞盘门/星/神八宫（星为九宫）不重复、无空缺"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="feipan")
        for key, pals in (("star", range(1, 10)), ("men", PAL8), ("shen", PAL8)):
            vals = [c.chart[p].get(key) for p in pals]
            assert all(vals), f"{y}-{m}-{d} {h}时 {key} 空缺: {vals}"
            assert len(set(vals)) == len(vals), f"{y}-{m}-{d} {h}时 {key} 重复: {vals}"
    print("✅ 飞盘门/星/神无重复空缺")


def test_feipan_zhongwu_shilu():
    """旬首仪落中五时，飞盘 _find_zhifu_palace 应返回 5（实落，不寄坤二）"""
    hit = None
    for m in range(1, 13):
        for d in (1, 8, 15, 22, 28):
            for h in range(0, 24, 3):
                c = QimenChart(2025, m, d, h, pan_style="feipan")
                if c.chart.get(5, {}).get("dipan") == c.xun_yi:
                    hit = c
                    break
            if hit:
                break
        if hit:
            break
    assert hit is not None, "年内应存在旬首仪落中五的飞盘"
    assert hit._find_zhifu_palace() == 5, (
        f"飞盘旬首仪{hit.xun_yi}在地盘中五，应实落取5，实得{hit._find_zhifu_palace()}"
    )
    print("✅ 飞盘中五实落正确")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 飞盘结构回归 {len(tests)} 项全部通过")


if __name__ == "__main__":
    run_all()