#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金口诀快速起课模块
四位定位：地分（方位）→将神（月将加时）→贵神（昼夜贵人）→人元（五子元遁）
"""
from dataclasses import dataclass
from typing import Dict, List
from lunar_python import Solar

# ============================================================
# 基础常量
# ============================================================
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_TO_IDX = {b:i for i,b in enumerate(EARTHLY_BRANCHES)}
HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEM_TO_IDX = {s:i for i,s in enumerate(HEAVENLY_STEMS)}

ELEMENT_MAP = {
    "甲":"木","乙":"木","寅":"木","卯":"木",
    "丙":"火","丁":"火","巳":"火","午":"火",
    "戊":"土","己":"土","辰":"土","戌":"土","丑":"土","未":"土",
    "庚":"金","辛":"金","申":"金","酉":"金",
    "壬":"水","癸":"水","亥":"水","子":"水",
}

# 月将表：中气后启用
YUE_JIANG_TABLE = {
    (2, 19): "亥", (3, 21): "戌", (4, 20): "酉",
    (5, 21): "申", (6, 21): "未", (7, 23): "午",
    (8, 23): "巳", (9, 23): "辰", (10, 24): "卯",
    (11, 22): "寅", (12, 22): "丑", (1, 20): "子",
}

def get_yue_jiang(year, month, day):
    return YUE_JIANG_TABLE.get((month, day), "巳")

# 贵人歌：日干 → (昼贵, 夜贵)
GUI_REN = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("巳", "卯"), "癸": ("巳", "卯"),
    "辛": ("午", "寅"),
}

SHEN_JIANG = ["贵人","螣蛇","朱雀","六合","勾陈","青龙","天空","白虎","太常","玄武","太阴","天后"]
SHEN_JIANG_ZHI = {"贵人":"子","螣蛇":"丑","朱雀":"寅","六合":"卯","勾陈":"辰","青龙":"巳",
                   "天空":"午","白虎":"未","太常":"申","玄武":"酉","太阴":"戌","天后":"亥"}
SHEN_JIANG_XIONG = {"贵人":"大吉","螣蛇":"凶","朱雀":"半凶","六合":"吉","勾陈":"凶","青龙":"大吉",
                     "天空":"凶","白虎":"大凶","太常":"吉","玄武":"凶","太阴":"吉","天后":"吉"}

WU_ZI_START = {"甲":0,"乙":1,"丙":2,"丁":3,"戊":4,"己":5,"庚":6,"辛":7,"壬":8,"癸":9}

def get_dun_gan(ri_gan, shi_zhi):
    idx = (WU_ZI_START[ri_gan] + BRANCH_TO_IDX[shi_zhi]) % 10
    return HEAVENLY_STEMS[idx]

def get_relation(e1, e2):
    if e1 == e2:
        return "比和"
    rels = [("木","火","生"),("火","土","生"),("土","金","生"),("金","水","生"),("水","木","生"),
            ("木","土","克"),("土","水","克"),("水","火","克"),("火","金","克"),("金","木","克")]
    for a,b,r in rels:
        if e1==a and e2==b:
            return r
    return "无关"

@dataclass
class JinKouJueResult:
    di_fen: str
    jiang_shen: str
    gui_shen: str
    ren_yuan: str
    tian_jiang_pan: Dict[str, str]
    relations: Dict[str, str]
    summary: str

class JinKouJueCalculator:
    def __init__(self, year, month, day, hour, direction="子"):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.direction = direction
        self._setup_lunar()
        self._calculate()

    def _setup_lunar(self):
        s = Solar(self.year, self.month, self.day, self.hour, 0, 0)
        l = s.getLunar()
        self.ri_gan = l.getDayInGanZhi()[0]
        self.ri_zhi = l.getDayInGanZhi()[1]
        self.shi_gan = l.getTimeInGanZhi()[0]
        self.shi_zhi = l.getTimeInGanZhi()[1]
        self.yue_zhi = l.getMonthInGanZhi()[1]
        self.yue_jiang = get_yue_jiang(self.year, self.month, self.day)
        self.gui_zhi = GUI_REN[self.ri_gan]

    def _calculate(self):
        self.di_fen = self.direction if self.direction in EARTHLY_BRANCHES else "子"
        offset = (BRANCH_TO_IDX[self.yue_jiang] - BRANCH_TO_IDX[self.shi_zhi] + 12) % 12
        self.jiang_shen = EARTHLY_BRANCHES[(BRANCH_TO_IDX[self.di_fen] + offset) % 12]
        is_day = 4 <= BRANCH_TO_IDX[self.shi_zhi] <= 17
        gui_zhi = self.gui_zhi[0] if is_day else self.gui_zhi[1]
        self.gui_shen = gui_zhi
        gui_gan = get_dun_gan(self.ri_gan, gui_zhi)
        ren_yuan_idx = (STEM_TO_IDX[gui_gan] + BRANCH_TO_IDX[self.di_fen]) % 10
        self.ren_yuan = HEAVENLY_STEMS[ren_yuan_idx]
        start_idx = BRANCH_TO_IDX[SHEN_JIANG_ZHI.get(self.ren_yuan, "子")]
        self.tian_jiang_pan = {}
        for i, jiang in enumerate(SHEN_JIANG):
            zhi = EARTHLY_BRANCHES[(start_idx + i) % 12]
            self.tian_jiang_pan[jiang] = zhi
        self.relations = {
            "人元": get_relation(ELEMENT_MAP[self.ren_yuan], ELEMENT_MAP[self.ri_gan]),
            "贵神": get_relation(ELEMENT_MAP[self.gui_shen], ELEMENT_MAP[self.ri_gan]),
            "将神": get_relation(ELEMENT_MAP[self.jiang_shen], ELEMENT_MAP[self.ri_gan]),
            "地分": get_relation(ELEMENT_MAP[self.di_fen], ELEMENT_MAP[self.ri_gan]),
        }
        self.summary = self._generate_summary()

    def _generate_summary(self):
        good = sum(1 for r in self.relations.values() if r in ("生","比和"))
        bad = sum(1 for r in self.relations.values() if r in ("克","被克"))
        if good >= 3:
            return "四位多吉，事端顺遂，可速决。"
        if good >= 2:
            return "吉多凶少，宜主动把握。"
        if good == bad:
            return "吉凶参半，宜守伺机。"
        return "四位多凶，事端阻滞，宜缓守。"

    def to_dict(self):
        return {"四位": {"人元": self.ren_yuan, "贵神": self.gui_shen, "将神": self.jiang_shen, "地分": self.di_fen},
                "十二神将落宫": self.tian_jiang_pan, "四位生克": self.relations, "简断": self.summary,
                "日柱": f"{self.ri_gan}{self.ri_zhi}", "时柱": f"{self.shi_gan}{self.shi_zhi}", "月将": self.yue_jiang}

    def to_text(self):
        L = []
        L.append("=" * 50)
        L.append("🔮 金口诀快速起课")
        L.append("=" * 50)
        L.append(f"日柱：{self.ri_gan}{self.ri_zhi}  时柱：{self.shi_gan}{self.shi_zhi}  月将：{self.yue_jiang}  方位：{self.direction}")
        L.append("")
        L.append("📐 四位定位：")
        L.append(f"  人元（遁干）：{self.ren_yuan}  [{self.relations['人元']}]")
        L.append(f"  贵神（贵人）：{self.gui_shen}  [{self.relations['贵神']}]")
        L.append(f"  将神（月将加时）：{self.jiang_shen}  [{self.relations['将神']}]")
        L.append(f"  地分（方位）：{self.di_fen}  [{self.relations['地分']}]")
        L.append("")
        L.append("🌟 十二神将落宫：")
        for jiang in SHEN_JIANG:
            zhi = SHEN_JIANG_ZHI[jiang]
            xiong = SHEN_JIANG_XIONG[jiang]
            emoji = {"大吉":"🟢","吉":"🟢","半凶":"🟠","凶":"🔴","大凶":"🔴"}.get(xiong,"⚪")
            rel = get_relation(ELEMENT_MAP[zhi], ELEMENT_MAP[self.ri_gan])
            rel_emoji = {"生":"🟢","克":"🔴","比和":"🟡","泄":"🔵","被克":"🟠"}.get(rel,"⚪")
            L.append(f"  {jiang}：{zhi} ({xiong} {emoji}) - 对日干 {rel} {rel_emoji}")
        L.append("")
        L.append(f"💡 简断：{self.summary}")
        L.append("=" * 50)
        return "\n".join(L)

def main():
    import argparse, json
    import os, sys
    # 定位共享历法库 sanzhi：兼容部署布局(shared_assets/sanzhi)与仓库布局(_shared)
    _d = os.path.dirname(os.path.abspath(__file__))
    while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
           and not os.path.isdir(os.path.join(_d, "_shared"))
           and os.path.dirname(_d) != _d):
        _d = os.path.dirname(_d)
    sys.path.insert(0, os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
                    else os.path.join(_d, "_shared"))
    from sanzhi import local_now
    parser = argparse.ArgumentParser(description="大六壬·金口诀快速起课")
    parser.add_argument("-q","--question",default="",help="求测问题")
    parser.add_argument("-y","--year",type=int,default=None)
    parser.add_argument("-m","--month",type=int,default=None)
    parser.add_argument("-d","--day",type=int,default=None)
    parser.add_argument("-H","--hour",type=int,default=None)
    parser.add_argument("-D","--direction",default="子",help="地分方位（子/丑/寅/卯...亥），默认子位")
    parser.add_argument("--json",action="store_true")
    args = parser.parse_args()
    now = local_now()
    calc = JinKouJueCalculator(args.year or now.year, args.month or now.month,
                                args.day or now.day, args.hour if args.hour is not None else now.hour,
                                args.direction)
    if args.json:
        print(json.dumps(calc.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(calc.to_text())

if __name__ == "__main__":
    main()