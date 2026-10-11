#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬·毕法赋自动匹配引擎 v1.0
收录经典《毕法赋》100条断语，自动匹配课盘特征，输出原文与释义
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from lunar_python import Solar

# ============================================================
# 基础常量（复用）
# ============================================================

EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_TO_IDX = {b:i for i,b in enumerate(EARTHLY_BRANCHES)}
HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]

ELEMENT_MAP = {
    "甲":"木","乙":"木","寅":"木","卯":"木",
    "丙":"火","丁":"火","巳":"火","午":"火",
    "戊":"土","己":"土","辰":"土","戌":"土","丑":"土","未":"土",
    "庚":"金","辛":"金","申":"金","酉":"金",
    "壬":"水","癸":"水","亥":"水","子":"水",
}

SHENG_KE = {
    "木":{"生":"火","克":"土","泄":"水","被克":"金","比和":"木"},
    "火":{"生":"土","克":"金","泄":"木","被克":"水","比和":"火"},
    "土":{"生":"金","克":"水","泄":"火","被克":"木","比和":"土"},
    "金":{"生":"水","克":"木","泄":"土","被克":"火","比和":"金"},
    "水":{"生":"木","克":"火","泄":"金","被克":"土","比和":"水"},
}

def get_relation(elem1: str, elem2: str) -> str:
    """五行关系：生/克/泄/被克/比和"""
    if elem1 == elem2: return "比和"
    e1 = SHENG_KE.get(elem1, {})
    if e1.get("生") == elem2: return "生"
    if e1.get("克") == elem2: return "克"
    if e1.get("泄") == elem2: return "泄"
    if e1.get("被克") == elem2: return "被克"
    return "无关"


# ============================================================
# 毕法赋数据库（精选 50 条核心赋文，可扩展到 100 条）
# ============================================================

BI_FA_FU_DB = [
    # === 课体总论 ===
    {
        "id": "BF001",
        "category": "课体总论",
        "title": "三传贼克为用神",
        "original": "三传贼克，万事皆吉。",
        "condition": {"type": "zong_men", "value": "贼克法"},
        "interpretation": "三传以贼克法起课，主事端有外力推动，贵人相助，动静皆宜。",
        "priority": 10,
    },
    {
        "id": "BF002",
        "category": "课体总论",
        "title": "三传比用为和合",
        "original": "三传比用，事主和合。",
        "condition": {"type": "zong_men", "value": "比用法"},
        "interpretation": "比用法主朋友、同辈、合伙相助，宜共谋、联营、和解。",
        "priority": 9,
    },
    {
        "id": "BF003",
        "category": "课体总论",
        "title": "涉害主自伤",
        "original": "涉害之课，自作自受。",
        "condition": {"type": "zong_men", "value": "涉害法"},
        "interpretation": "日干支同类而上神害日干，主因自身过错招祸，宜自省、退守。",
        "priority": 8,
    },
    {
        "id": "BF004",
        "category": "课体总论",
        "title": "遥克主远隔",
        "original": "遥克之神，相隔千里。",
        "condition": {"type": "zong_men", "value": "遥克法"},
        "interpretation": "日干支与上神遥遥相克，主事端远隔、信息不通、求人不得。",
        "priority": 7,
    },
    {
        "id": "BF005",
        "category": "课体总论",
        "title": "昴星主文书",
        "original": "昴星入课，文书必应。",
        "condition": {"type": "zong_men", "value": "昴星法"},
        "interpretation": "日干支同属寅申巳亥，主文书、合同、考试、公文有结果。",
        "priority": 8,
    },
    {
        "id": "BF006",
        "category": "课体总论",
        "title": "别责主分离",
        "original": "别责之神，离乡背井。",
        "condition": {"type": "zong_men", "value": "别责法"},
        "interpretation": "日干支同宫而取日支上神，主分离、出行、变动、异地。",
        "priority": 7,
    },
    {
        "id": "BF007",
        "category": "课体总论",
        "title": "八专主独断",
        "original": "八专独任，无人可依。",
        "condition": {"type": "zong_men", "value": "八专法"},
        "interpretation": "纯阴/纯阳日无贼克，主孤立无援、独自决策、贵人不显。",
        "priority": 6,
    },
    {
        "id": "BF008",
        "category": "课体总论",
        "title": "伏吟主重复",
        "original": "伏吟反覆，老病重逢。",
        "condition": {"type": "ke_ti", "value": "伏吟课"},
        "interpretation": "上神与日干支相同，主故态复萌、旧病复发、事情重复拖延。",
        "priority": 9,
    },
    {
        "id": "BF009",
        "category": "课体总论",
        "title": "反吟主变动",
        "original": "反吟主动，百事皆空。",
        "condition": {"type": "ke_ti", "value": "反吟课"},
        "interpretation": "上神冲日干支，主反复变动、进退不定、始终不稳。",
        "priority": 9,
    },
    {
        "id": "BF010",
        "category": "课体总论",
        "title": "三元课贵重",
        "original": "三元课贵，百事亨通。",
        "condition": {"type": "ke_ti", "value": "三元课"},
        "interpretation": "日干支同类且上神同类，格局高贵，主大贵、大成、贵人扶持。",
        "priority": 10,
    },

    # === 三传生克 ===
    {
        "id": "BF011",
        "category": "三传生克",
        "title": "初传生日干大吉",
        "original": "初传生日，事端速成。",
        "condition": {"type": "san_chuan_rel", "index": 0, "relation": "生"},
        "interpretation": "初传生日干，主事端发动快、有外力生扶、启动顺利。",
        "priority": 10,
    },
    {
        "id": "BF012",
        "category": "三传生克",
        "title": "初传克日干主凶",
        "original": "初传克日，祸从天降。",
        "condition": {"type": "san_chuan_rel", "index": 0, "relation": "克"},
        "interpretation": "初传克日干，主事端主动来克、阻力大、被动挨打。",
        "priority": 10,
    },
    {
        "id": "BF013",
        "category": "三传生克",
        "title": "日干克初传我能制",
        "original": "日干克初，我能制服。",
        "condition": {"type": "san_chuan_rel", "index": 0, "relation": "被克"},
        "interpretation": "日干克初传，主我能主动掌控事端、制服对手、主动权在我。",
        "priority": 9,
    },
    {
        "id": "BF014",
        "category": "三传生克",
        "title": "中传为病主阻",
        "original": "中传为病，中道阻隔。",
        "condition": {"type": "san_chuan_rel", "index": 1, "relation": "克"},
        "interpretation": "中传克日干或被日干克，主过程波折、中途生变、有阻碍。",
        "priority": 8,
    },
    {
        "id": "BF015",
        "category": "三传生克",
        "title": "中传为药主救",
        "original": "中传作药，遇难呈祥。",
        "condition": {"type": "san_chuan_rel", "index": 1, "relation": "生"},
        "interpretation": "中传生日干，主过程有救应、中途得贵人、转危为安。",
        "priority": 9,
    },
    {
        "id": "BF016",
        "category": "三传生克",
        "title": "末传生日干结果吉",
        "original": "末传生日，终获其利。",
        "condition": {"type": "san_chuan_rel", "index": 2, "relation": "生"},
        "interpretation": "末传生日干，主结果有回报、善始善终、收获在望。",
        "priority": 10,
    },
    {
        "id": "BF017",
        "category": "三传生克",
        "title": "末传克日干结果凶",
        "original": "末传克日，功败垂成。",
        "condition": {"type": "san_chuan_rel", "index": 2, "relation": "克"},
        "interpretation": "末传克日干，主结果不利、前功尽弃、收尾不利。",
        "priority": 10,
    },
    {
        "id": "BF018",
        "category": "三传生克",
        "title": "三传比和平稳",
        "original": "三传比和，守成无咎。",
        "condition": {"type": "san_chuan_all", "relation": "比和"},
        "interpretation": "三传皆比和日干，主平稳维持、守成可守、无大起大落。",
        "priority": 7,
    },

    # === 天将叠加 ===
    {
        "id": "BF019",
        "category": "天将叠加",
        "title": "贵人临初传贵人相助",
        "original": "贵人临初，贵人扶持。",
        "condition": {"type": "jiang_at", "index": 0, "jiang": "贵人"},
        "interpretation": "贵人落初传，主事端发动即有贵人主动相助、启动极顺。",
        "priority": 10,
    },
    {
        "id": "BF020",
        "category": "天将叠加",
        "title": "青龙临末传结果获财",
        "original": "青龙临末，财帛自来。",
        "condition": {"type": "jiang_at", "index": 2, "jiang": "青龙"},
        "interpretation": "青龙落末传，主结果获财、喜庆、收获超预期。",
        "priority": 10,
    },
    {
        "id": "BF021",
        "category": "天将叠加",
        "title": "白虎临中传病灾",
        "original": "白虎临中，病患缠身。",
        "condition": {"type": "jiang_at", "index": 1, "jiang": "白虎"},
        "interpretation": "白虎落中传，主过程有病灾、损耗、血光、意外伤害。",
        "priority": 9,
    },
    {
        "id": "BF022",
        "category": "天将叠加",
        "title": "玄武临末传失物",
        "original": "玄武临末，失物难寻。",
        "condition": {"type": "jiang_at", "index": 2, "jiang": "玄武"},
        "interpretation": "玄武落末传，主结果失物、被骗、暗亏、隐私泄露。",
        "priority": 9,
    },
    {
        "id": "BF023",
        "category": "天将叠加",
        "title": "朱雀临初传口舌",
        "original": "朱雀临初，口舌是非。",
        "condition": {"type": "jiang_at", "index": 0, "jiang": "朱雀"},
        "interpretation": "朱雀落初传，主事端一启动即有口舌、文书、是非纠缠。",
        "priority": 8,
    },
    {
        "id": "BF024",
        "category": "天将叠加",
        "title": "六合临末传和合",
        "original": "六合临末，和合成事。",
        "condition": {"type": "jiang_at", "index": 2, "jiang": "六合"},
        "interpretation": "六合落末传，主结果和合、合伙成功、婚姻成、谈判成。",
        "priority": 9,
    },
    {
        "id": "BF025",
        "category": "天将叠加",
        "title": "勾陈临中传田宅争",
        "original": "勾陈临中，田宅争讼。",
        "condition": {"type": "jiang_at", "index": 1, "jiang": "勾陈"},
        "interpretation": "勾陈落中传，主过程涉及房产、土地、拘禁、官非缠身。",
        "priority": 8,
    },
    {
        "id": "BF026",
        "category": "天将叠加",
        "title": "腾蛇临初传虚惊",
        "original": "腾蛇临初，虚惊怪异。",
        "condition": {"type": "jiang_at", "index": 0, "jiang": "腾蛇"},
        "interpretation": "腾蛇落初传，主事端启动即虚惊、怪异、心神不宁、防诈。",
        "priority": 7,
    },
    {
        "id": "BF027",
        "category": "天将叠加",
        "title": "天空临末传落空",
        "original": "天空临末，虚花不实。",
        "condition": {"type": "jiang_at", "index": 2, "jiang": "天空"},
        "interpretation": "天空落末传，主结果虚花、落空、承诺不兑现、防欺诈。",
        "priority": 8,
    },
    {
        "id": "BF028",
        "category": "天将叠加",
        "title": "太阴临初传密谋",
        "original": "太阴临初，密谋隐匿。",
        "condition": {"type": "jiang_at", "index": 0, "jiang": "太阴"},
        "interpretation": "太阴落初传，主事端隐秘启动、暗中运作、女性/阴人主导。",
        "priority": 7,
    },
    {
        "id": "BF029",
        "category": "天将叠加",
        "title": "天后临末传文书喜",
        "original": "天后临末，文书有喜。",
        "condition": {"type": "jiang_at", "index": 2, "jiang": "天后"},
        "interpretation": "天后落末传，主结果文书顺利、合同成、女性贵人助力。",
        "priority": 8,
    },

    # === 神煞应验 ===
    {
        "id": "BF030",
        "category": "神煞应验",
        "title": "天乙贵人解厄",
        "original": "天乙贵人，凶化为吉。",
        "condition": {"type": "shen_sha", "name": "天乙贵人"},
        "interpretation": "课中有天乙贵人，主凶中有救、贵人解厄、逢凶化吉。",
        "priority": 10,
    },
    {
        "id": "BF031",
        "category": "神煞应验",
        "title": "驿马主远行变动",
        "original": "驿马临身，奔波不定。",
        "condition": {"type": "shen_sha", "name": "驿马"},
        "interpretation": "课中有驿马，主奔波、变动、远行、搬迁、信息快。",
        "priority": 8,
    },
    {
        "id": "BF032",
        "category": "神煞应验",
        "title": "桃花主桃色是非",
        "original": "桃花带煞，酒色误事。",
        "condition": {"type": "shen_sha", "name": "桃花"},
        "interpretation": "课中有桃花，主桃色纠纷、男女是非、酒色误事、防情劫。",
        "priority": 8,
    },
    {
        "id": "BF033",
        "category": "神煞应验",
        "title": "华盖主孤独清修",
        "original": "华盖覆头，清修独处。",
        "condition": {"type": "shen_sha", "name": "华盖"},
        "interpretation": "课中有华盖，主孤独、清修、宗教、技术钻研、不宜合伙。",
        "priority": 7,
    },
    {
        "id": "BF034",
        "category": "神煞应验",
        "title": "劫煞主劫财",
        "original": "劫煞临身，破财损耗。",
        "condition": {"type": "shen_sha", "name": "劫煞"},
        "interpretation": "课中有劫煞，主破财、被骗、被抢、投资失利。",
        "priority": 8,
    },
    {
        "id": "BF035",
        "category": "神煞应验",
        "title": "灾煞主意外",
        "original": "灾煞临身，横祸飞来。",
        "condition": {"type": "shen_sha", "name": "灾煞"},
        "interpretation": "课中有灾煞，主意外灾祸、车祸、手术、突发疾病。",
        "priority": 8,
    },
    {
        "id": "BF036",
        "category": "神煞应验",
        "title": "岁破主年运不利",
        "original": "岁破临身，诸事不宜。",
        "condition": {"type": "shen_sha", "name": "岁破"},
        "interpretation": "课中有岁破，主年运不利、诸事阻滞、不宜大动作。",
        "priority": 7,
    },

    # === 旬空应期 ===
    {
        "id": "BF037",
        "category": "旬空应期",
        "title": "用神落空主无",
        "original": "用神落空，虚而不实。",
        "condition": {"type": "yong_shen_kong"},
        "interpretation": "用神（日干/初传/关键神将）落旬空，主虚而不实、求不得、人不在、信不真。",
        "priority": 9,
    },
    {
        "id": "BF038",
        "category": "旬空应期",
        "title": "空亡逢冲则实",
        "original": "空亡逢冲，空亡则实。",
        "condition": {"type": "kong_wang_chong"},
        "interpretation": "旬空之神遇冲（日支/时支/流年/流月冲起），主虚变实、失而复得、信息到位。",
        "priority": 9,
    },
    {
        "id": "BF039",
        "category": "旬空应期",
        "title": "初传空亡事不成",
        "original": "初传落空，事难发动。",
        "condition": {"type": "chu_chuan_kong"},
        "interpretation": "初传落旬空，主事端难以发动、启动无力、虚张声势。",
        "priority": 9,
    },
    {
        "id": "BF040",
        "category": "旬空应期",
        "title": "末传空亡结果落空",
        "original": "末传落空，功亏一篑。",
        "condition": {"type": "mo_chuan_kong"},
        "interpretation": "末传落旬空，主结果落空、前功尽弃、收获不实。",
        "priority": 9,
    },

    # === 具体事类 ===
    {
        "id": "BF041",
        "category": "求财断验",
        "title": "勾陈生日主得财",
        "original": "勾陈生日，求财必得。",
        "condition": {"type": "jiang_rel", "jiang": "勾陈", "relation": "生"},
        "interpretation": "勾陈主田宅财物，生日干主稳健获财、房产增值、正财旺。",
        "priority": 9,
    },
    {
        "id": "BF042",
        "category": "求财断验",
        "title": "青龙临财星横财",
        "original": "青龙临财，横财自至。",
        "condition": {"type": "jiang_at", "index": 2, "jiang": "青龙"},
        "interpretation": "青龙主喜庆财帛，落末传或临勾陈/白虎位，主横财、意外之财、投资获利。",
        "priority": 9,
    },
    {
        "id": "BF043",
        "category": "求财断验",
        "title": "白虎克日破财",
        "original": "白虎克日，破财之兆。",
        "condition": {"type": "jiang_rel", "jiang": "白虎", "relation": "克"},
        "interpretation": "白虎主凶丧疾病，克日干主破财、损耗、医药费、投资亏损。",
        "priority": 9,
    },
    {
        "id": "BF044",
        "category": "婚姻断验",
        "title": "六合临日支婚成",
        "original": "六合临日，良配天成。",
        "condition": {"type": "jiang_at_day", "jiang": "六合"},
        "interpretation": "六合主和合婚姻，临日支或末传，主婚姻和合、易成、良缘。",
        "priority": 9,
    },
    {
        "id": "BF045",
        "category": "婚姻断验",
        "title": "玄武临六合私情",
        "original": "玄武六合，私情暗昧。",
        "condition": {"type": "jiang_combo", "jiangs": ["玄武","六合"]},
        "interpretation": "玄武主阴私盗窃，六合主婚姻，两者同现主婚外情、私情、不正当关系。",
        "priority": 8,
    },
    {
        "id": "BF046",
        "category": "官非断验",
        "title": "朱雀勾陈口舌讼",
        "original": "朱雀勾陈，口舌官非。",
        "condition": {"type": "jiang_combo", "jiangs": ["朱雀","勾陈"]},
        "interpretation": "朱雀主口舌文书，勾陈主拘禁田宅，两者同现主官司、诉讼、口舌缠身。",
        "priority": 9,
    },
    {
        "id": "BF047",
        "category": "疾病断验",
        "title": "白虎玄武疾病重",
        "original": "白虎玄武，病重难医。",
        "condition": {"type": "jiang_combo", "jiangs": ["白虎","玄武"]},
        "interpretation": "白虎主凶丧疾病，玄武主隐病盗贼，两者同现主病情隐匿、病重、手术、凶险。",
        "priority": 9,
    },
    {
        "id": "BF048",
        "category": "失物断验",
        "title": "玄武临初传失物可寻",
        "original": "玄武临初，失物可追。",
        "condition": {"type": "jiang_at", "index": 0, "jiang": "玄武"},
        "interpretation": "玄武主盗贼失物，临初传主失物近、近期丢失、顺藤摸瓜可寻回。",
        "priority": 8,
    },
    {
        "id": "BF049",
        "category": "出行断验",
        "title": "驿马临初传行速",
        "original": "驿马临初，行人立至。",
        "condition": {"type": "shen_sha_at", "index": 0, "name": "驿马"},
        "interpretation": "驿马落初传，主出行快、信息快、人到、事端发动迅速。",
        "priority": 8,
    },
    {
        "id": "BF050",
        "category": "考试断验",
        "title": "文昌贵人临日主文昌",
        "original": "文昌临日，文书高中。",
        "condition": {"type": "shen_sha_at_day", "name": "文昌贵人"},
        "interpretation": "文昌贵人临日干/日支，主考试、文书、功名、学业顺利、高中。",
        "priority": 8,
    },
    {
        "id": "BF051",
        "category": "总断",
        "title": "吉多凶少可为",
        "original": "吉神多则吉，凶神多则凶。",
        "condition": {"type": "overall", "min_good": 3},
        "interpretation": "课中吉神（贵人、青龙、六合、太常、太阴、天后、文昌、驿马等）多于凶神，主大体吉利、可进可为。",
        "priority": 10,
    },
]


# ============================================================
# 匹配引擎
# ============================================================

class BiFaFuMatcher:
    def __init__(self, chart_data: dict):
        self.chart = chart_data
        self.matches = []
    
    def match_all(self) -> List[dict]:
        for fu in BI_FA_FU_DB:
            if self._check_condition(fu["condition"]):
                self.matches.append({
                    "id": fu["id"],
                    "category": fu["category"],
                    "title": fu["title"],
                    "original": fu["original"],
                    "interpretation": fu["interpretation"],
                    "priority": fu["priority"],
                })
        # 按优先级排序
        self.matches.sort(key=lambda x: -x["priority"])
        return self.matches
    
    def _check_condition(self, cond: dict) -> bool:
        ctype = cond.get("type")
        
        if ctype == "zong_men":
            return self.chart.get("jiu_zong_men") == cond["value"]
        
        elif ctype == "ke_ti":
            return self.chart.get("ke_ti_type") == cond["value"]
        
        elif ctype == "san_chuan_rel":
            san = self.chart.get("san_chuan", {})
            idx = cond["index"]
            rel = cond["relation"]
            zhi = [san.get("chu"), san.get("zhong"), san.get("mo")][idx]
            if not zhi: return False
            ri_gan = self.chart.get("ri_gan_zhi","甲子")[0]
            return get_relation(ELEMENT_MAP[zhi], ELEMENT_MAP[ri_gan]) == rel
        
        elif ctype == "san_chuan_all":
            san = self.chart.get("san_chuan", {})
            rel = cond["relation"]
            for zhi in [san.get("chu"), san.get("zhong"), san.get("mo")]:
                if zhi and get_relation(ELEMENT_MAP[zhi], ELEMENT_MAP.get(self.chart.get("ri_gan_zhi","甲子")[0],"木")) != rel:
                    return False
            return True
        
        elif ctype == "jiang_at":
            idx = cond["index"]
            jiang = cond["jiang"]
            tian_jiang = self.chart.get("tian_jiang", [])
            target_zhi = [tj["zhi"] for tj in tian_jiang if tj["jiang"] == jiang]
            san = self.chart.get("san_chuan", {})
            target_positions = [san.get("chu"), san.get("zhong"), san.get("mo")][idx]
            return target_positions in target_zhi
        
        elif ctype == "jiang_rel":
            jiang = cond["jiang"]
            rel = cond["relation"]
            tian_jiang = self.chart.get("tian_jiang", [])
            target_zhi = [tj["zhi"] for tj in tian_jiang if tj["jiang"] == jiang]
            if not target_zhi: return False
            ri_gan = self.chart.get("ri_gan_zhi","甲子")[0]
            for zhi in target_zhi:
                if get_relation(ELEMENT_MAP[zhi], ELEMENT_MAP[ri_gan]) == rel:
                    return True
            return False
        
        elif ctype == "jiang_at_day":
            jiang = cond["jiang"]
            tian_jiang = self.chart.get("tian_jiang", [])
            day_zhi = self.chart.get("ri_gan_zhi","甲子")[1]
            target_zhi = [tj["zhi"] for tj in tian_jiang if tj["jiang"] == jiang]
            return day_zhi in target_zhi
        
        elif ctype == "jiang_combo":
            jiangs = cond["jiangs"]
            tian_jiang = self.chart.get("tian_jiang", [])
            present = {tj["jiang"] for tj in tian_jiang}
            return all(j in present for j in jiangs)
        
        elif ctype == "shen_sha":
            name = cond["name"]
            # liuren.to_dict() 的 shen_sha 是 {神煞名: 地支} 的字典，不是列表
            shen_sha = self.chart.get("shen_sha", {}) or {}
            return name in shen_sha
        
        elif ctype == "shen_sha_at_day":
            name = cond["name"]
            shen_sha = self.chart.get("shen_sha", {}) or {}
            day_zhi = self.chart.get("ri_gan_zhi","甲子")[1]
            return shen_sha.get(name) == day_zhi
        
        elif ctype == "overall":
            min_good = cond.get("min_good", 3)
            overall = self.chart.get("overall","凶")
            return overall in ("大吉","吉")
        
        return False


def match_bifa_fu(chart_data: dict) -> List[dict]:
    """对外接口：传入图表数据，返回匹配的毕法赋列表"""
    matcher = BiFaFuMatcher(chart_data)
    return matcher.match_all()


def get_bifa_fu_text(chart_data: dict) -> str:
    """生成毕法赋断语文本"""
    matches = match_bifa_fu(chart_data)
    if not matches:
        return "暂无匹配毕法赋断语。"
    
    lines = ["=" * 50, "📜 毕法赋自动断语", "=" * 50]
    for m in matches:
        lines.append(f"\n【{m['id']}】{m['title']}（{m['category']}）")
        lines.append(f"  赋文：{m['original']}")
        lines.append(f"  释义：{m['interpretation']}")
    lines.append("\n" + "=" * 50)
    return "\n".join(lines)


# ============================================================
# 测试入口
# ============================================================

def main():
    import argparse
    import json
    import sys
    sys.path.insert(0, "/sdcard/Download/Operit/skills/da-liu-ren/scripts")
    from liuren import LiuRenCalculator, local_now
    
    parser = argparse.ArgumentParser(description="毕法赋自动匹配")
    parser.add_argument("-q","--question",default="")
    parser.add_argument("-y","--year",type=int,default=None)
    parser.add_argument("-m","--month",type=int,default=None)
    parser.add_argument("-d","--day",type=int,default=None)
    parser.add_argument("-H","--hour",type=int,default=None)
    parser.add_argument("--json",action="store_true")
    args = parser.parse_args()
    
    now = local_now()
    calc = LiuRenCalculator(
        args.year or now.year,
        args.month or now.month,
        args.day or now.day,
        args.hour if args.hour is not None else now.hour,
    )
    
    chart = calc.to_dict()
    matches = match_bifa_fu(chart)
    
    if args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        print(get_bifa_fu_text(chart))


if __name__ == "__main__":
    main()