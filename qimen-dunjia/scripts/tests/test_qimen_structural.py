#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""奇门遁甲·转盘结构回归测试（防复发）

覆盖此前全绿但实际错误、以及从未被测试过的结构：
  - 旬首/旬首仪/空亡按【时柱】取（时家奇门）
  - 转盘九星序列 == 本位星序，且源码不得再另写字面量
  - 值符加时干：值符落宫 = 时干宫；值符星随旬首仪
  - 甲时天盘伏吟（天盘 == 地盘）
  - 八宫星/门/神互不重复、无空缺

运行：python3 tests/test_qimen_structural.py 或 pytest tests/
"""
import inspect
import os
import re
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

from qimen import QimenChart, STAR_RING, STAR_HOME, YI_TO_STAR, EIGHT_PALACE_ORDER  # noqa: E402

PAL8 = [1, 2, 3, 4, 6, 7, 8, 9]
TBL = "甲子戊甲戌己甲申庚甲午辛甲辰壬甲寅癸"


def _xun_by_time(ganzhi):
    for k in range(60):
        if "甲乙丙丁戊己庚辛壬癸"[k % 10] + "子丑寅卯辰巳午未申酉戌亥"[k % 12] == ganzhi:
            return TBL[k // 10 * 3:k // 10 * 3 + 3]
    raise AssertionError(f"非法时柱 {ganzhi}")


def test_star_ring_is_canonical():
    """转盘星序须为本位星序（曾误写为 蓬任冲辅英芮柱心，5 宫错位）"""
    assert STAR_RING == [STAR_HOME[p] for p in EIGHT_PALACE_ORDER]
    assert STAR_RING == ["天蓬", "天芮", "天冲", "天辅", "天心", "天柱", "天任", "天英"]
    print("✅ 转盘九星序列正确")


def test_no_hardcoded_star_ring_in_renpan():
    """_make_renpan 不得再硬写星序字面量（唯一来源应为 STAR_RING）"""
    src = inspect.getsource(QimenChart._make_renpan)
    assert not re.findall(r"star_names\s*=", src), "又出现了硬写的 star_names"
    print("✅ 星序无重复字面量")


def test_xun_by_hour():
    """旬首/旬首仪/空亡按【时柱】取，不得用日柱"""
    c = QimenChart(2026, 8, 31, 16)          # 日柱丁丑 / 时柱戊申
    t = _xun_by_time(c.ganzhi_time)
    assert c.ganzhi_day == "丁丑" and c.ganzhi_time == "戊申"
    assert (c.xun_shou, c.xun_yi) == (t[:2], t[2]) == ("甲辰", "壬")
    assert c.kong_wang == ["寅", "卯"], f"甲辰旬空寅卯，实际{c.kong_wang}"
    print("✅ 旬首按时柱取")


def test_zhifu_falls_on_hour_stem_palace():
    """值符加时干：值符落宫 = 时干在地盘之宫；值符星随旬首仪"""
    c = QimenChart(2026, 8, 31, 16)
    zbf = c._zhifu_palace()
    assert c.chart[zbf]["dipan"] == c.shi_gan, "值符落宫地盘应为时干"
    assert c.chart[zbf]["star"] == YI_TO_STAR[c.xun_yi], "值符宫应见值符星"
    assert c.chart[zbf]["shen"] == "值符", "值符落宫应见值符神"
    print(f"✅ 值符落宫={zbf}（时干宫）值符星={c.chart[zbf]['star']}")


def test_zhifu_star_follows_yi():
    """值符星顺序：戊蓬/己芮/庚冲/辛辅/壬寄芮/癸心"""
    assert YI_TO_STAR == {"戊": "天蓬", "己": "天芮", "庚": "天冲",
                          "辛": "天辅", "壬": "天芮", "癸": "天心"}
    seen = set()
    d0 = date(2026, 1, 1)
    for k in range(80):
        d = d0 + timedelta(days=k)
        for h in (0, 6, 12, 18):
            c = QimenChart(d.year, d.month, d.day, h)
            zbf = c._zhifu_palace()
            assert c.chart[zbf]["star"] == YI_TO_STAR[c.xun_yi], (
                f"{d} {h}时 仪={c.xun_yi} 值符宫{zbf}星={c.chart[zbf]['star']}"
            )
            seen.add(c.xun_yi)
    assert seen == set("戊己庚辛壬癸"), f"未覆盖全部六仪：{seen}"
    print(f"✅ 值符星随旬首仪（覆盖六仪 {sorted(seen)}）")


def test_jia_hour_fuyin():
    """甲时天盘须伏吟（天盘 == 地盘，含中五）"""
    hits = []
    d0 = date(2026, 1, 1)
    for k in range(400):
        d = d0 + timedelta(days=k)
        for h in (0, 12):
            from lunar_python import Solar
            if Solar(d.year, d.month, d.day, h, 0, 0).getLunar().getTimeInGanZhi()[0] == "甲":
                hits.append((d, h))
        if len(hits) >= 6:
            break
    assert len(hits) >= 6
    for d, h in hits[:6]:
        c = QimenChart(d.year, d.month, d.day, h)
        assert c.shi_gan == "甲"
        for p in range(1, 10):
            assert c.chart[p]["tianpan"] == c.chart[p]["dipan"], (
                f"{d} {h}时 宫{p} 天盘{c.chart[p]['tianpan']}≠地盘{c.chart[p]['dipan']}（应伏吟）"
            )
    print(f"✅ 甲时伏吟（验 {len(hits[:6])} 盘）")


def test_renpan_no_duplicate():
    """八宫星/门/神互不重复、无空缺"""
    for y, m, dd, h in ((2026, 1, 15, 10), (2026, 2, 4, 16), (2026, 8, 27, 16), (2025, 3, 8, 0)):
        c = QimenChart(y, m, dd, h)
        for key in ("star", "men", "shen"):
            vals = [c.chart[p].get(key) for p in PAL8]
            assert all(vals), f"{y}-{m}-{dd} {h}时 {key} 有空缺: {vals}"
            assert len(set(vals)) == 8, f"{y}-{m}-{dd} {h}时 {key} 有重复: {vals}"
    print("✅ 八宫星/门/神无重复空缺")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 转盘结构回归 {len(tests)} 项全部通过")


if __name__ == "__main__":
    run_all()