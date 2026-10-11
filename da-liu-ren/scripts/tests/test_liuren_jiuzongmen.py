#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大六壬·九宗门结构性回归（八专法/遥克法 取传订正）

文献依据：
  八专——《六壬视斯》"两课无克号八专，阳日时神顺行三。
        阴日阴神逆三数，中末都来干上眠。"
  遥克——"先取神遥来克日，无神克与日相交。复有两神来克日，
        或有日去克两神，当择与日干比者用，阳日用阳、阴用阴。"

运行：python3 tests/test_liuren_jiuzongmen.py 或 pytest tests/
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

from liuren import (LiuRenCalculator, BRANCH_TO_IDX, EARTHLY_BRANCHES,  # noqa: E402
                    GAN_GONG, ELEMENT_MAP, get_relation)

YANG_GAN = "甲丙戊庚壬"


def _find_bazhuan(n_days=800, limit=6):
    out = []
    d0 = date(2026, 1, 1)
    for k in range(n_days):
        d = d0 + timedelta(days=k)
        for h in (0, 8, 16):
            c = LiuRenCalculator(d.year, d.month, d.day, h)
            if c.jiu_zong_men == "八专法":
                out.append(c)
                if len(out) >= limit:
                    return out
    return out


def _recount(c, start, forward):
    """按口诀于天盘自 start 顺/逆数三神（含起点）"""
    inv = {v: k for k, v in c.tianpan.items()}
    cur = start
    for _ in range(2):
        di = inv[cur]
        idx = (BRANCH_TO_IDX[di] + (1 if forward else -1)) % 12
        cur = c.tianpan[EARTHLY_BRANCHES[idx]]
    return cur


def test_aliases_removed():
    """死代码（空实现/占位类）应已清除"""
    import liuren as L
    for name in ("get_current_jieqi", "DefaultWeatherAnalyzer", "LunarData"):
        assert not hasattr(L, name), f"{name} 应已删除（占位/死代码）"
    print("✅ 占位死代码已清除")


def test_bazhuan_zhongmo_is_gan_shang():
    """八专：中传、末传俱取干上神"""
    cases = _find_bazhuan()
    assert cases, "应能扫出八专课样本"
    for c in cases:
        gs = c.tianpan[GAN_GONG[c.ri_gan]]
        assert c.san_chuan["zhong"] == gs, f"中传应取干上神{gs}，实得{c.san_chuan['zhong']}"
        assert c.san_chuan["mo"] == gs, f"末传应取干上神{gs}，实得{c.san_chuan['mo']}"
    print(f"✅ 八专中末传俱取干上神（验 {len(cases)} 课）")


def test_bazhuan_chu_by_koujue():
    """八专初传：阳日第一课上神顺数三、阴日第四课上神逆数三"""
    cases = _find_bazhuan()
    assert cases, "应能扫出八专课样本"
    yang_n = yin_n = 0
    for c in cases:
        yang = c.ri_gan in YANG_GAN
        start = c.si_ke[0]["shang"] if yang else c.si_ke[3]["shang"]
        want = _recount(c, start, yang)
        assert c.san_chuan["chu"] == want, (
            f"{c.ri_gan}日 初传应{want}（口诀数三神），实得{c.san_chuan['chu']}"
        )
        assert c.san_chuan["chu"] != start, "初传不应等于起点（须数三神）"
        yang_n += yang
        yin_n += (not yang)
    print(f"✅ 八专初传合口诀（阳日{yang_n} 阴日{yin_n}）")


def test_bieze_trigger_condition():
    """别责法：课程去重=3（有一课上下同神，4课退化为3课）且无克 才触发

    根因回归：旧 _is_bieze 用「8个格位（4课×上下神）去重==3」判据，
    因第1/2课、第3/4课首尾相接（前课上神=后课下神），独立支上限仅 6，
    去重==3 数学上不可能达成 → 别责法恒不触发（死分支）。
    正确判据：课程（上下神对）去重==3。"""
    from liuren import GAN_GONG, ELEMENT_MAP, get_relation, _liushi_idx
    from lunar_python import Solar
    from datetime import date, timedelta

    BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

    def ke_xia_ke(si_ke):
        """四课上下神是否相克（下神克上神或上神克下神）"""
        for ke in si_ke:
            e_d = ELEMENT_MAP.get(ke["di"], "")
            e_s = ELEMENT_MAP.get(ke["shang"], "")
            if e_d and e_s and get_relation(e_d, e_s) == "克":
                return True
            if e_d and e_s and get_relation(e_s, e_d) == "克":
                return True
        return False

    def distinct_courses(c):
        return len({(k["di"], k["shang"]) for k in c.si_ke})

    hit = 0
    d0 = date(2026, 1, 1)
    for k in range(800):
        d = d0 + timedelta(days=k)
        for h in (0, 8, 16):
            c = LiuRenCalculator(d.year, d.month, d.day, h)
            if c.jiu_zong_men != "别责法":
                continue
            hit += 1
            # 触发必须满足：课程去重==3 且无克 且非八专
            assert distinct_courses(c) == 3, f"{d} {h}时 别责法应课程去重=3，实得{distinct_courses(c)}"
            assert not c._find_zei_ke(), f"{d} {h}时 别责法应无克"
            assert GAN_GONG[c.ri_gan] != c.ri_zhi, f"{d} {h}时 别责法非八专日"
            for key in ("chu", "zhong", "mo"):
                assert c.san_chuan.get(key), f"{d} {h}时 别责法 {key} 为空"
            if hit >= 4:
                break
    assert hit >= 4, "应能扫出别责法样本（修复前恒不触发）"
    print(f"✅ 别责法触发条件正确（验 {hit} 课）")


def test_yaoke_picks_birike():
    """遥克：蒿矢优先弹射；多候选时取与日干阴阳相同者（比用）"""
    hit = multi = 0
    d0 = date(2026, 1, 1)
    for k in range(600):
        d = d0 + timedelta(days=k)
        for h in (0, 12):
            c = LiuRenCalculator(d.year, d.month, d.day, h)
            if c.jiu_zong_men != "遥克法":
                continue
            hit += 1
            gan_yang = c.ri_gan in YANG_GAN
            chu = c.san_chuan["chu"]
            assert chu, "遥克初传不应为空"
            # 初传须来自某课上神，且为"遥克/被遥克"之神
            src = [ke for ke in c.si_ke if ke["shang"] == chu]
            assert src, f"初传{chu}应来自某课上神"
            # 仅当候选多于一个时，才要求"比者用"
            cands = [ke for ke in c.si_ke
                     if ELEMENT_MAP.get(ke["shang"]) and
                     (get_relation(ELEMENT_MAP[ke["shang"]], ELEMENT_MAP[c.ri_gan]) == "克")]
            if len(cands) == 0:
                cands = [ke for ke in c.si_ke
                         if get_relation(ELEMENT_MAP[c.ri_gan], ELEMENT_MAP.get(ke["shang"], "")) == "克"]
            if len(cands) > 1:
                multi += 1
                bi = [ke for ke in cands if (BRANCH_TO_IDX[ke["shang"]] % 2 == 0) == gan_yang]
                if len(bi) == 1:
                    assert chu == bi[0]["shang"], (
                        f"{c.ri_gan}日 多候选时应取比者{bi[0]['shang']}，实得{chu}"
                    )
    assert hit > 0, "应能扫出遥克课样本"
    print(f"✅ 遥克取用正确（验 {hit} 课，其中多候选 {multi} 课）")


def test_all_courses_have_sanchuan():
    """各门三传齐备性"""
    n = 0
    d0 = date(2026, 1, 1)
    for k in range(200):
        d = d0 + timedelta(days=k)
        for h in (0, 8, 16):
            c = LiuRenCalculator(d.year, d.month, d.day, h)
            n += 1
            for key in ("chu", "zhong", "mo"):
                assert c.san_chuan.get(key), f"{d} {h}时 {c.jiu_zong_men} 的 {key} 为空"
    print(f"✅ 三传齐备（验 {n} 课）")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 九宗门结构回归 {len(tests)} 项全部通过")


if __name__ == "__main__":
    run_all()