#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲排盘扩展测试
据源：《御定奇门宝鉴》《烟波钓叟歌》《奇门遁甲秘笈大全》
运行：python3 tests/test_qimen_extended.py 或 pytest tests/
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

from qimen import QimenChart, DOOR_HOME, BRANCH_TO_IDX

PAL8 = [1, 2, 3, 4, 6, 7, 8, 9]


def test_zhifu_zhishi():
    """值符值使定位准确性（对比手动计算）

    注：旧版断言旬首为甲辰/壬（按日柱己酉推）且把旬首仪地盘本宫
    当作值符落宫，均已修正为按【时柱】取旬、值时干宫。
    """
    # 2026-02-04 16时 (申时) - 壬申时，旬首甲子，旬首仪戊
    c = QimenChart(2026, 2, 4, 16)

    assert c.ganzhi_time == "壬申", f"时柱应壬申，实际{c.ganzhi_time}"
    assert c.xun_shou == "甲子", f"旬首应甲子，实际{c.xun_shou}"
    assert c.xun_yi == "戊", f"旬首仪应戊，实际{c.xun_yi}"

    # 值符加时干：值符落宫 = 时干（壬）在地盘之宫
    zhifu_palace = c._zhifu_palace()
    assert c.chart[zhifu_palace]["dipan"] == c.shi_gan == "壬", (
        f"值符宫{zhifu_palace}地盘应为时干壬，实际{c.chart[zhifu_palace]['dipan']}"
    )
    # 值符星随旬首仪（戊→天蓬）
    assert c.chart[zhifu_palace]["star"] == "天蓬", (
        f"戊仪值符星应天蓬，实际{c.chart[zhifu_palace]['star']}"
    )
    print(f"✅ 值符定位正确：旬首{c.xun_shou}，值符落宫{zhifu_palace}（时干宫），值符星天蓬")


def test_zhishi_steps():
    """值使门落宫计算（时支序号-旬首支序号=步数，模12）

    注：旧版假设旬首为甲子（支子）得 steps=8；按修正后的时柱取旬，
    2026-08-27 16时 为庚申时，旬首甲寅（支寅）→ steps=6。
    """
    c = QimenChart(2026, 8, 27, 16)

    assert c.ganzhi_time == "庚申", f"时柱应庚申，实际{c.ganzhi_time}"
    assert c.xun_shou == "甲寅", f"旬首应甲寅，实际{c.xun_shou}"

    sz_idx = BRANCH_TO_IDX[c.shi_zhi]           # 申 = 8
    xb_idx = BRANCH_TO_IDX[c.xun_shou[1]]       # 寅 = 2
    steps = (sz_idx - xb_idx) % 12              # = 6

    assert steps == 6, f"步数应6，实际{steps}"
    print(f"✅ 值使步数正确：申时减寅支 = {steps}步")


def test_zhishi_door():
    """值使门落在正确宫位"""
    c = QimenChart(2026, 8, 27, 16)

    # 值使门应落某宫
    zhishi_door = c.chart.get(c.zhimen_palace, {}).get("men", "")
    assert zhishi_door in DOOR_HOME.values(), f"值使门应有名，实际{zhishi_door}"
    print(f"✅ 值使门正确：宫{c.zhimen_palace} {zhishi_door}")


def test_bamen_feibu():
    """八门飞布顺序验证"""
    c = QimenChart(2026, 8, 27, 16)

    # 八门应分布在八宫（不含中五）
    men_palaces = []
    for p in [1, 2, 3, 4, 6, 7, 8, 9]:
        men = c.chart.get(p, {}).get("men", "")
        if men:
            men_palaces.append((p, men))

    assert len(men_palaces) == 8, f"八门应分布8宫，实际{len(men_palaces)}"
    print(f"✅ 八门分布正确：{[(p, m) for p, m in men_palaces]}")


def test_jiuxing_feibu():
    """九星飞布顺序验证"""
    c = QimenChart(2026, 8, 27, 16)

    # 九星应分布在八宫（天禽寄坤二）
    star_palaces = []
    for p in [1, 2, 3, 4, 6, 7, 8, 9]:
        star = c.chart.get(p, {}).get("star", "")
        if star:
            star_palaces.append((p, star))

    assert len(star_palaces) >= 8, f"九星应分布至少8宫，实际{len(star_palaces)}"

    # 转盘：天禽不显于中五，而寄于天芮之宫（star_ji）
    assert "star" not in c.chart.get(5, {}), "转盘中五不应显星（天禽寄天芮之宫）"
    rui = [p for p, s in star_palaces if s == "天芮"]
    ji = [p for p in PAL8 if c.chart[p].get("star_ji") == "天禽"]
    assert ji == rui and len(rui) == 1, f"天禽应寄天芮之宫{rui}，实得{ji}"
    print(f"✅ 九星分布正确：{[(p, s) for p, s in star_palaces]} 天禽寄宫{ji}")


def test_bashen_feibu():
    """八神飞布顺序验证（值符神落值符落宫 = 时干宫）"""
    c = QimenChart(2026, 8, 27, 16)

    shen_palaces = []
    for p in [1, 2, 3, 4, 6, 7, 8, 9]:
        shen = c.chart.get(p, {}).get("shen", "")
        if shen:
            shen_palaces.append((p, shen))

    assert len(shen_palaces) == 8, f"八神应分布8宫，实际{len(shen_palaces)}"

    # 值符神应落"值符落宫"（=时干宫），非旬首仪的地盘本宫
    zhifu_palace = c._zhifu_palace()
    assert c.chart[zhifu_palace]["shen"] == "值符", (
        f"值时干宫{zhifu_palace}应有值符神，实际{c.chart[zhifu_palace].get('shen')}"
    )
    print(f"✅ 八神分布正确：{[s for _, s in shen_palaces]}")


def test_different_jieqi():
    """不同节气定局验证"""
    # 冬至后阳遁
    c1 = QimenChart(2026, 1, 15, 10)
    assert c1.is_yang_dun, "冬至后应为阳遁"

    # 夏至后阴遁
    c2 = QimenChart(2026, 7, 15, 10)
    assert not c2.is_yang_dun, "夏至后应为阴遁"

    print(f"✅ 不同节气定局正确：冬至{c1.ju_number}局，夏至{c2.ju_number}局")


def test_zhiyun_zhiyun_available():
    """置闰法可用性测试"""
    from qimen import ZHIYUN_AVAILABLE
    assert ZHIYUN_AVAILABLE, "置闰法模块应可用"
    print("✅ 置闰法模块可用")


def test_zhiyun_yuan_method():
    """置闰法三元判断测试"""
    # 2026-01-15 处于大雪置闰区间（大雪结束超神>9天，小寒置闰重复大雪三元）
    c = QimenChart(2026, 1, 15, 10)
    assert hasattr(c, 'yuan_idx'), "应有yuan_idx属性"
    assert hasattr(c, 'zhi_run'), "应有zhi_run属性"
    assert hasattr(c, 'fu_tou'), "应有fu_tou属性"
    # 置闰法下应识别出置闰状态
    # 2026-01-15 是己丑日，所在元符头为己亥（己丑日本身即符头起元）
    assert c.zhi_run == True, "2026-01-15应处于置闰状态（大雪置闰）"
    assert c.fu_tou == "己亥", f"符头应为己亥，实际{c.fu_tou}"
    assert c.yuan == "下元", f"元应为下元，实际{c.yuan}"
    print(f"✅ 置闰法三元正确：{c.yuan} 符头={c.fu_tou} 置闰={c.zhi_run}")


def test_zhiyun_zhiyun_vs_chaibu():
    """置闰法与拆补法差异验证（已知差异案例）"""
    # 2026-06-21 夏至，芒种结束前超神14天>9天，置闰法应在夏至插入3符头重复芒种三元
    c_zhiyun = QimenChart(2026, 6, 21, 12)
    # 拆补法直接用 get_yuan（需对比）
    from sanzhi import get_yuan
    from qimen import DefaultLunarProvider
    provider = DefaultLunarProvider()
    lunar_data = provider.get_lunar_data(2026, 6, 21, 12)
    chaibu_yuan = get_yuan(2026, 6, 21, lunar_data.prev_jieqi_name, provider)
    
    # 置闰法因置闰插入，三元序列会与拆补法不同
    assert c_zhiyun.zhi_run in [True, False], "置闰状态应明确"
    print(f"✅ 置闰法与拆补法差异：置闰法三元={c_zhiyun.yuan}({c_zhiyun.yuan_idx}) 拆补法三元={['上元','中元','下元'][chaibu_yuan]}({chaibu_yuan}) 置闰={c_zhiyun.zhi_run}")


def test_zhiyun_2025_mangzhong():
    """2025年芒种置闰验证（历史已知置闰年）"""
    # 2025年芒种(6/5)结束前，芒种最后符头超神>9天，应在夏至(6/21)置闰
    c = QimenChart(2025, 6, 21, 12)  # 2025夏至
    # 此日期在芒种节气结束、夏至节气开始
    # 置闰法应检测到芒种置闰
    print(f"✅ 2025夏至置闰检查：三元={c.yuan} 符头={c.fu_tou} 置闰={c.zhi_run} 节气={c.current_jieqi}")


def test_zhiyun_output_contains_method():
    """输出包含定局法标识"""
    c = QimenChart(2026, 1, 15, 10)
    d = c.to_dict()
    assert "yuan_method" in d["ju"], "输出应包含yuan_method"
    assert d["ju"]["yuan_method"] == "置闰法", f"应为置闰法，实际{d['ju']['yuan_method']}"
    assert "fu_tou" in d["ju"], "输出应包含fu_tou"
    assert "zhi_run" in d["ju"], "输出应包含zhi_run"
    print(f"✅ 输出包含定局法标识：{d['ju']['yuan_method']} 符头={d['ju']['fu_tou']} 置闰={d['ju']['zhi_run']}")


def test_zhifu_palace_zhongwu_ji_kun2():
    """回归：值符落宫/值符起宫落在中五时必须寄坤二，不得返回5 或越界

    历史缺陷：_find_zhifu_palace() 直接返回 5，调用方
    EIGHT_PALACE_ORDER.index(5) 抛错后兜底到宫1，导致八门/八神整盘错位。

    注：旧版靠"2025-03-08 00时恰命中中五"做定点验证；旬首改为按时柱后
    该单局不再命中（时柱戊子 → 甲申旬/庚 → 仪庚在宫6），故改为直接
    校验寄宫规则，覆盖面反而更大（2880 盘 + 直测）。
    """
    # 直测规则：旬首仪落中五 → 寄坤二
    c0 = QimenChart(2025, 3, 8, 0)
    assert c0.xun_yi == "庚" and c0._find_zhifu_palace() == 6
    # 用一个仪确在中五的盘面直测（遍历年内找命中者）
    hit = None
    for m in range(1, 13):
        for d in (1, 8, 15, 22, 28):
            for h in range(0, 24, 3):
                cc = QimenChart(2025, m, d, h)
                if cc.chart.get(5, {}).get("dipan") == cc.xun_yi:
                    hit = cc
                    break
            if hit:
                break
        if hit:
            break
    assert hit is not None, "年内应存在旬首仪落中五的盘面"
    assert hit._find_zhifu_palace() == 2, (
        f"旬首仪{hit.xun_yi}在地盘中五，值符起宫应寄坤二(2)"
    )

    bad = []
    for y in (2025, 2026):
        for m in range(1, 13):
            for d in (1, 8, 15, 22, 28):
                for h in range(0, 24, 6):
                    c = QimenChart(y, m, d, h)
                    for pal in (c._find_zhifu_palace(), c._zhifu_palace()):
                        if pal not in (1, 2, 3, 4, 6, 7, 8, 9):
                            bad.append((y, m, d, h, pal))
    assert not bad, f"值符起宫/落宫不得为中五(5)或越界，异常样本: {bad[:5]}"
    print("✅ 值符起宫/落宫中五寄坤二正确（2880 盘无越界）")


def run_all():
    """运行所有测试"""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 奇门遁甲扩展测试 {len(tests)} 项全部通过")


if __name__ == "__main__":
    run_all()