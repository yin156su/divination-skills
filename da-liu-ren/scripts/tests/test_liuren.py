#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬排盘引擎回归测试
据源：《六壬大全》卷一首传法、《毕法赋》
运行：python3 tests/test_liuren.py 或 pytest tests/
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

from liuren import LiuRenCalculator


def test_four_courses():
    """四课生成：癸酉日申时 四课正确"""
    c = LiuRenCalculator(2026, 8, 27, 16)
    assert len(c.si_ke) == 4, "应有四课"
    # 第一课干上：癸寄丑，月将巳加申 → 丑上戌
    assert c.si_ke[0]["di"] == "丑", f"癸日寄丑，实际{c.si_ke[0]['di']}"
    assert c.si_ke[0]["shang"] == "戌", f"丑上应戌，实际{c.si_ke[0]['shang']}"
    # 第三课支上：酉上应午
    assert c.si_ke[2]["di"] == "酉", f"酉日支，实际{c.si_ke[2]['di']}"
    assert c.si_ke[2]["shang"] == "午", f"酉上应午，实际{c.si_ke[2]['shang']}"
    print("✅ 四课生成正确")


def test_san_chuan_zeike():
    """贼克起法：癸酉日申时 三传午→卯→子"""
    c = LiuRenCalculator(2026, 8, 27, 16)
    assert c.jiu_zong_men == "贼克法", f"起法应贼克法，实际{c.jiu_zong_men}"
    assert c.san_chuan["chu"] == "午", f"初传应午，实际{c.san_chuan['chu']}"
    assert c.san_chuan["zhong"] == "卯", f"中传应卯，实际{c.san_chuan['zhong']}"
    assert c.san_chuan["mo"] == "子", f"末传应子，实际{c.san_chuan['mo']}"
    print("✅ 贼克起法三传正确")


def test_she_hai():
    """涉害起法：己丑日巳时 三传巳→丑→酉（涉害法）

    四课：未上卯 / 卯上亥 / 丑上酉 / 酉上巳。
    上克下候选：卯克己、巳克酉；日干己属阴，卯、巳皆阴 → 涉害。
    卯本家顺行至未历 0 克；巳本家顺行至酉历 0 克 → 深浅相等。
    按《六壬大全》"先孟后仲"：巳属四孟、卯属四仲 → 取巳。
    """
    c = LiuRenCalculator(2026, 1, 15, 10)
    assert "涉害" in c.jiu_zong_men, f"起法应涉害，实际{c.jiu_zong_men}"
    assert c.san_chuan["chu"] == "巳", f"初传应巳，实际{c.san_chuan['chu']}"
    assert c.san_chuan["zhong"] == "丑", f"中传应丑，实际{c.san_chuan['zhong']}"
    assert c.san_chuan["mo"] == "酉", f"末传应酉，实际{c.san_chuan['mo']}"
    print("✅ 涉害起法正确")


def test_month_jiang():
    """月将按中气定：8-27处暑后为巳将，1-15小寒后为丑将"""
    c1 = LiuRenCalculator(2026, 8, 27, 16)
    c2 = LiuRenCalculator(2026, 1, 15, 10)
    assert c1.yue_jiang == "巳", f"处暑后应巳将，实际{c1.yue_jiang}"
    assert c2.yue_jiang == "丑", f"小寒后应丑将，实际{c2.yue_jiang}"
    print("✅ 月将按中气定正确")


def test_kong_wang():
    """空亡：癸酉日（甲子旬）空戌亥；己丑日（甲申旬）空午未"""
    c1 = LiuRenCalculator(2026, 8, 27, 16)
    c2 = LiuRenCalculator(2026, 1, 15, 10)
    assert c1.kong_wang == ["戌", "亥"], f"癸酉日空戌亥，实际{c1.kong_wang}"
    assert c2.kong_wang == ["午", "未"], f"己丑日空午未，实际{c2.kong_wang}"
    print("✅ 空亡正确")


def test_tian_jiang():
    """十二天将：数量12且含贵人"""
    c = LiuRenCalculator(2026, 8, 27, 16)
    assert len(c.tian_jiang_list) == 12, "应有12天将"
    names = [t["jiang"] for t in c.tian_jiang_list]
    assert "贵人" in names and "白虎" in names
    print("✅ 十二天将正确")


def test_yinyang_gan_gong():
    """日干寄宫：甲寅乙辰丙巳戊巳丁未己未庚申辛戌壬亥癸丑"""
    from liuren import GAN_GONG
    expect = {"甲":"寅","乙":"辰","丙":"巳","丁":"未","戊":"巳",
              "己":"未","庚":"申","辛":"戌","壬":"亥","癸":"丑"}
    for g, z in expect.items():
        assert GAN_GONG[g] == z, f"{g}应寄{z}，实际{GAN_GONG[g]}"
    print("✅ 日干寄宫正确")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 大六壬排盘 {len(tests)} 项测试全部通过")


if __name__ == "__main__":
    run_all()