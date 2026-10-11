#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中五寄坤二 回归测试（转盘）

文献依据（两个独立来源口径一致）：
  「转盘问事局用寄二宫法」「中五宫的信息，寄在坤二宫，与二宫的信息放在一起来看」
  「天禽星经常出现在天芮星旁边，天芮星在哪个宫，天禽星就在哪个宫」
  另参《烟波钓叟歌》"天禽寄坤二"

断言：
  A 转盘：天禽不得显于中五（星寄他宫），天芮所在宫带 star_ji=天禽
  B 转盘：坤二宫带 dipan_ji == 中五地盘干
  C 飞盘：不走转盘寄宫，中五实落得天禽，且无 star_ji/dipan_ji
  D 转盘天盘干恒为 X+X（中五不参与环移）—— 寄宫不改变这一点，
    故 _match_geju 仍按盘式跳过转盘中五

运行：python3 tests/test_qimen_jigong.py 或 pytest tests/
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
       and not os.path.isdir(os.path.join(_d, "_shared"))
       and os.path.dirname(_d) != _d):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
                else os.path.join(_d, "_shared"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from qimen import QimenChart  # noqa: E402

PAL8 = [1, 2, 3, 4, 6, 7, 8, 9]
CASES = ((2026, 8, 31, 16), (2026, 1, 15, 10), (2026, 2, 4, 16),
         (2025, 3, 8, 0), (2026, 7, 15, 12))


def test_zhuanpan_tianqin_follows_tianrui():
    """转盘：天禽随天芮——天芮所在宫带 star_ji=天禽，中五不显天禽"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="zhuanpan")
        assert "star" not in c.chart.get(5, {}), f"{y}-{m}-{d} {h}时 转盘中五不应显星"
        rui = [p for p in PAL8 if c.chart[p].get("star") == "天芮"]
        ji = [p for p in PAL8 if c.chart[p].get("star_ji") == "天禽"]
        assert len(rui) == 1, f"天芮应恰在一宫: {rui}"
        assert ji == rui, f"天禽应寄天芮之宫{rui}，实得{ji}"
    print("✅ 转盘天禽随天芮")


def test_zhuanpan_dipan_ji_kun2():
    """转盘：中五地盘干寄坤二宫（dipan_ji == 宫5地盘干）"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="zhuanpan")
        di5 = c.chart[5].get("dipan")
        assert di5, "中五应有地盘干"
        assert c.chart[2].get("dipan_ji") == di5, (
            f"{y}-{m}-{d} {h}时 坤二应寄中五千{di5}，实得{c.chart[2].get('dipan_ji')}"
        )
        # 并行开关已废：不应再输出 dipan_note
        assert "dipan_note" not in c.chart[5], "旧的 dipan_note 标注应已不再产生"
    print("✅ 转盘中五干寄坤二")


def test_feipan_not_jigong():
    """飞盘：九星实落九宫（天禽为其中一位，未必在中五），不得出现转盘寄宫字段"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="feipan")
        stars = [c.chart[p].get("star") for p in range(1, 10)]
        assert all(stars), f"飞盘九星应实落九宫: {stars}"
        assert len(set(stars)) == 9, f"飞盘九星不得重复: {stars}"
        assert "天禽" in stars, f"飞盘九星应含天禽（实落，非寄）: {stars}"
        for p in range(1, 10):
            assert "star_ji" not in c.chart[p], f"飞盘宫{p}不应有 star_ji"
            assert "dipan_ji" not in c.chart[p], f"飞盘宫{p}不应有 dipan_ji"
    print("✅ 飞盘九星实落九宫，不走转盘寄宫")


def test_zhuanpan_tianpan_same_gan():
    """转盘中五仍为 X+X（寄宫不改变环移口径），故判格仍须跳过中五"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="zhuanpan")
        a, b = c.chart[5].get("dipan"), c.chart[5].get("tianpan")
        assert a == b, f"{y}-{m}-{d} {h}时 转盘中五应为同干，实得{a}+{b}"
    print("✅ 转盘中五恒同干（判格跳过之依据仍然成立）")


def test_text_shows_jigong():
    """文本输出须体现寄宫信息（否则用户看不见）"""
    c = QimenChart(2026, 8, 31, 16, pan_style="zhuanpan")
    txt = c.to_text()
    assert "寄天禽" in txt, "输出应显示天禽寄于天芮之宫"
    assert "｜寄" in txt, "输出应显示中五干寄坤二"
    print("✅ 文本输出含寄宫信息")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 中五寄坤二 回归 {len(tests)} 项全部通过")


if __name__ == "__main__":
    run_all()