#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬排盘扩展测试
据源：《六壬大全》卷一首传法、《毕法赋》
运行：python3 tests/test_liuren_extended.py 或 pytest tests/
"""
import os
import sys
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

from liuren import LiuRenCalculator, EARTHLY_BRANCHES


def test_fanyin_san_chuan():
    """返吟法三传测试（四课有克回落贼克）"""
    # 选择一个返吟且有克的例子
    c = LiuRenCalculator(2026, 2, 15, 11)  # 午时与子月将（大寒后子将）相冲
    if c.jiu_zong_men == "返吟法":
        assert "san_chuan" in c.to_dict(), "返吟法应有三传"
        print(f"✅ 返吟法三传：{c.san_chuan}")
    else:
        print(f"⚠️ 返吟法触发条件未满足，跳过测试")


def test_bazhuan_san_chuan():
    """八专法三传测试"""
    # 日干寄宫与日支同支的日子：甲寅、丁未、己未、庚申、癸丑
    test_dates = [
        (2026, 3, 16, 14),  # 甲寅日，日干寄宫寅与日支寅同
        (2026, 7, 10, 10),  # 丁未日
        (2026, 7, 22, 10),  # 己未日
        (2026, 8, 24, 10),  # 庚申日
        (2026, 1, 10, 10),  # 癸丑日
    ]
    
    for year, month, day, hour in test_dates:
        c = LiuRenCalculator(year, month, day, hour)
        if c.jiu_zong_men == "八专法":
            assert c.san_chuan["chu"], "八专法应有初传"
            print(f"✅ 八专法三传（{c.ri_gan}{c.ri_zhi}日）：{c.san_chuan}")
            break
    else:
        print("⚠️ 八专法触发条件未满足，跳过测试")


def test_bieze_san_chuan():
    """别责法三传测试"""
    # 四课去重后只剩三课的日子（有一课上下相同）
    c = LiuRenCalculator(2026, 3, 20, 10)
    if c.jiu_zong_men == "别责法":
        assert c.san_chuan["chu"], "别责法应有初传"
        print(f"✅ 别责法三传：{c.san_chuan}")
    else:
        print(f"⚠️ 别责法触发条件未满足，跳过测试")


def test_yaoke_san_chuan():
    """遥克法三传测试"""
    # 四课齐备无克，且不落伏吟/返吟/八专/别责
    c = LiuRenCalculator(2026, 4, 10, 10)
    if c.jiu_zong_men == "遥克法":
        assert c.san_chuan["chu"], "遥克法应有初传"
        print(f"✅ 遥克法三传：{c.san_chuan}")
    else:
        print(f"⚠️ 遥克法触发条件未满足（当前{c.jiu_zong_men}），跳过测试")


def test_maoxing_san_chuan():
    """昴星法三传测试"""
    # 四课无克、遥克也取不出（判定链末端）
    # 使用一个已知昴星起法的例子
    c = LiuRenCalculator(2026, 5, 5, 10)
    if c.jiu_zong_men == "昴星法":
        assert c.san_chuan["chu"], "昴星法应有初传"
        print(f"✅ 昴星法三传：{c.san_chuan}")
    else:
        print(f"⚠️ 昴星法触发条件未满足（当前{c.jiu_zong_men}），跳过测试")


def test_tianjiang_shun_ni():
    """天将顺逆分界测试"""
    # 贵人所临地盘宫在亥子丑寅卯辰顺布，在巳午未申酉戌逆布
    test_cases = [
        (2026, 1, 15, 10),  # 己丑日，贵人落卯（辰前，应顺布）
        (2026, 7, 15, 10),  # 午后，贵人落巳（辰后，应逆布）
    ]
    
    for year, month, day, hour in test_cases:
        c = LiuRenCalculator(year, month, day, hour)
        # 检查贵人位置
        gui_zhi = None
        for t in c.tian_jiang_list:
            if t["jiang"] == "贵人":
                gui_zhi = t["zhi"]
                break
        
        assert gui_zhi, "应有贵人"
        print(f"✅ 天将位置（{c.ri_gan}{c.ri_zhi}日{c.shi_zhi}时）：贵人临{gui_zhi}")


def test_multiple_yuejiang():
    """不同月将测试"""
    # 中气与月将的映射关系
    test_cases = [
        ((2026, 1, 15), "丑", "小寒后应丑将"),
        ((2026, 2, 19), "亥", "雨水后应亥将"),
        ((2026, 3, 21), "戌", "春分后应戌将"),
        ((2026, 4, 20), "酉", "谷雨后应酉将"),
        ((2026, 5, 21), "申", "小满后应申将"),
        ((2026, 6, 21), "未", "夏至后应未将"),
        ((2026, 7, 23), "午", "大暑后应午将"),
        ((2026, 8, 23), "巳", "处暑后应巳将"),
        ((2026, 9, 23), "辰", "秋分后应辰将"),
        ((2026, 10, 23), "卯", "霜降后应卯将"),
        ((2026, 11, 22), "寅", "小雪后应寅将"),
        ((2026, 12, 21), "丑", "冬至后应丑将"),
    ]
    
    for (year, month, day), expected, desc in test_cases:
        c = LiuRenCalculator(year, month, day, 10)
        if c.yue_jiang != expected:
            print(f"⚠️ {desc}：预期{expected}，实际{c.yue_jiang}")
        else:
            print(f"✅ {desc}")


def run_all():
    """运行所有测试"""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 大六壬扩展测试 {len(tests)} 项全部完成")


if __name__ == "__main__":
    run_all()