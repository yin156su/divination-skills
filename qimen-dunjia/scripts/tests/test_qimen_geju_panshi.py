#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格局判定 × 盘式 回归测试

锁定本轮修掉的问题：
  A 转盘中五为寄宫，其天盘干抄自地盘（干对恒 X+X），**不得**据此报同干格
  B 飞盘中五实落得真干，**应当**照常判格
  C 转盘格局不得落在宫5；飞盘可以
  D 格局库自身无"同对异名"歧义

运行：python3 tests/test_qimen_geju_panshi.py 或 pytest tests/
"""
import json
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

from qimen import QimenChart  # noqa: E402

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "geju_db.json")
CASES = ((2026, 1, 1, 12), (2026, 1, 15, 10), (2026, 2, 4, 16), (2026, 8, 31, 16),
         (2025, 3, 8, 0), (2026, 7, 15, 12))


def test_geju_db_no_ambiguity():
    """格局库无同对异名（一干对只对应一个格名）"""
    entries = json.load(open(DB, encoding="utf-8"))["geju"]
    seen = {}
    for e in entries:
        k = (e["tianpan"], e["dipan"])
        assert k not in seen, f"{k[0]}加{k[1]} 有歧义: {seen[k]} / {e['name']}"
        seen[k] = e["name"]
    print(f"✅ 格局库 {len(entries)} 条无歧义")


def test_geju_db_full_coverage():
    """格局库须覆盖全部 81 干对（乙丙丁戊己庚辛壬癸 × 同）

    2026-10-10 前仅 71 对，缺 10 对；该 10 对永不触发，属静默漏判。
    已据《奇门遁甲秘笈大全》卷二·十干克应诀补录。
    """
    entries = json.load(open(DB, encoding="utf-8"))["geju"]
    stems = "乙丙丁戊己庚辛壬癸"
    have = {(e["tianpan"], e["dipan"]) for e in entries}
    missing = [(a, b) for a in stems for b in stems if (a, b) not in have]
    assert not missing, f"仍缺 {len(missing)} 对: {missing}"
    assert len(entries) == 81, f"应为 81 条，实际 {len(entries)}"
    # 每条必备字段
    for e in entries:
        for k in ("tianpan", "dipan", "name", "level", "desc"):
            assert e.get(k), f"{e} 缺字段 {k}"
        assert e["tianpan"] in stems and e["dipan"] in stems
    print("✅ 格局库 81/81 全覆盖且字段完整")


def test_zhuanpan_zhongwu_never_matches():
    """转盘：中五不得产出格局（其天盘干抄自地盘，X+X 是数据镜像）"""
    for y, m, d, h in CASES:
        c = QimenChart(y, m, d, h, pan_style="zhuanpan")
        pal = [g["palace"] for g in c._match_geju()]
        assert 5 not in pal, f"{y}-{m}-{d} {h}时 转盘中五产出格局: {pal}"
        # 同时确认中五干对确实是 X+X（说明该分支必然误报，跳过是对的）
        a, b = c.chart[5].get("dipan"), c.chart[5].get("tianpan")
        assert a == b, "转盘中五天盘干应抄自地盘"
    print("✅ 转盘中五不判格")


def test_zhuanpan_zhongwu_all_same_gan():
    """转盘中五 480 盘全为 X+X——这是跳过中五的直接依据"""
    d0 = date(2026, 1, 1)
    n = same = 0
    for k in range(30):
        dd = d0 + timedelta(days=k)
        for h in (0, 12):
            c = QimenChart(dd.year, dd.month, dd.day, h, pan_style="zhuanpan")
            a, b = c.chart[5].get("dipan"), c.chart[5].get("tianpan")
            n += 1
            same += (a == b)
    assert same == n, f"转盘中五应 100% 同干，实得 {same}/{n}"
    print(f"✅ 转盘中五 {same}/{n} 全为同干（故不可判伏吟类）")


def test_feipan_zhongwu_matches():
    """飞盘：中五实落，可以产出格局（且非恒同干）"""
    found = same = n = 0
    d0 = date(2026, 1, 1)
    for k in range(30):
        dd = d0 + timedelta(days=k)
        for h in (0, 12):
            c = QimenChart(dd.year, dd.month, dd.day, h, pan_style="feipan")
            a, b = c.chart[5].get("dipan"), c.chart[5].get("tianpan")
            n += 1
            same += (a == b)
            found += any(g["palace"] == 5 for g in c._match_geju())
    assert same < n, f"飞盘中五不应恒同干，实得 {same}/{n}"
    assert found > 0, "飞盘中五应能产出格局"
    print(f"✅ 飞盘中五可判格（同干 {same}/{n}，产出格局 {found} 盘）")


def test_panshi_differs():
    """两盘式格局结果本应不同（SKILL.md 旧称"与盘式无关"是错的）"""
    diff = 0
    for y, m, d, h in CASES:
        z = QimenChart(y, m, d, h, pan_style="zhuanpan")
        f = QimenChart(y, m, d, h, pan_style="feipan")
        zs = sorted(g["name"] for g in z._match_geju())
        fs = sorted(g["name"] for g in f._match_geju())
        diff += (zs != fs)
    assert diff == len(CASES), f"两盘式格局应全部不同，实际相同 {len(CASES)-diff} 盘"
    print(f"✅ 两盘式格局结果不同（{diff}/{len(CASES)} 盘）")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\n🎉 格局×盘式 回归 {len(tests)} 项全部通过")


if __name__ == "__main__":
    run_all()