#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬排盘核心实现
据源：《六壬大全》卷一首传法、《毕法赋》、 《六壬指南》
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import date
from dataclasses import dataclass
from lunar_python import Solar

# ============================================================
# 统一调试日志前缀
# ============================================================
DEBUG_PREFIX = "[DEBUG-LIUREN]"

def dlog(msg: str):
    """统一调试日志输出"""
    print(f"{DEBUG_PREFIX} {msg}", file=sys.stderr)

def _hour12(hour: Optional[int]) -> int:
    """仅供「不带时辰的干支/节气查询」用：缺省取正午。
    注意不可写成 `hour or 12`——那会把合法的 0 点（子时）也换成正午，
    使子时排盘与节气边界判定出错。"""
    return 12 if hour is None else hour

# 添加共享库路径
# 定位共享历法库 sanzhi：兼容部署布局(shared_assets/sanzhi)与仓库布局(_shared)
_d = os.path.dirname(os.path.abspath(__file__))
while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
       and not os.path.isdir(os.path.join(_d, "_shared"))
       and os.path.dirname(_d) != _d):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
                else os.path.join(_d, "_shared"))
from sanzhi import local_now
# 传统天气占断（新增）
from sanzhi.weather_traditional import analyze_weather, TraditionalWeather

# ============================================================
# 自包含基础常量（原从 sanzhi 导入）
# ============================================================

HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
STEM_TO_IDX = {s:i for i,s in enumerate(HEAVENLY_STEMS)}
BRANCH_TO_IDX = {b:i for i,b in enumerate(EARTHLY_BRANCHES)}
LIUSHI_JIAZI = [f"{HEAVENLY_STEMS[i%10]}{EARTHLY_BRANCHES[i%12]}" for i in range(60)]

# 旬首→空亡映射（六十甲子每旬后两位为空）
XUN_KONG = {
    "甲子": ["戌","亥"], "甲戌": ["申","酉"], "甲申": ["午","未"],
    "甲午": ["辰","巳"], "甲辰": ["寅","卯"], "甲寅": ["子","丑"],
}

def _liushi_idx(gan: str, zhi: str) -> int:
    """干支在六十甲子中的位置 (0-59)"""
    si = STEM_TO_IDX[gan]
    bi = BRANCH_TO_IDX[zhi]
    for i in range(si, 60, 10):
        if i % 12 == bi:
            return i
    return 0

def get_kong_wang(ri_gan, ri_zhi):
    """获取旬空：日柱所在旬的后两位地支"""
    xun_shou = LIUSHI_JIAZI[_liushi_idx(ri_gan, ri_zhi) // 10 * 10]
    return XUN_KONG.get(xun_shou, [])

# 日干寄宫（阳干寄禄，阴干寄禄后一辰）
GAN_GONG = {
    "甲":"寅", "乙":"辰", "丙":"巳", "丁":"未",
    "戊":"巳", "己":"未", "庚":"申", "辛":"戌",
    "壬":"亥", "癸":"丑",
}

# 五行
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
def get_relation(e1, e2):
    if e1 == e2: return "比和"
    rels = [("木","火","生"),("火","土","生"),("土","金","生"),("金","水","生"),("水","木","生"),
            ("木","土","克"),("土","水","克"),("水","火","克"),("火","金","克"),("金","木","克")]
    for a,b,r in rels:
        if e1==a and e2==b: return r
    return "无关"

# 地支关系
LIU_CHONG = {"子":"午","丑":"未","寅":"申","卯":"酉","辰":"戌","巳":"亥",
             "午":"子","未":"丑","申":"寅","酉":"卯","戌":"辰","亥":"巳"}
LIU_HE = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
          "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
SAN_HE = {"申":"子","子":"辰","辰":"申",
          "寅":"午","午":"戌","戌":"寅",
          "巳":"酉","酉":"丑","丑":"巳",
          "亥":"卯","卯":"未","未":"亥"}
SAN_HUI = {"寅卯辰":"木","巳午未":"火","申酉戌":"金","亥子丑":"水","辰戌丑未":"土"}
# 三刑（据通行刑律，用于伏吟法中末传取刑）
# 子卯相刑（无礼之刑）；寅巳申相刑（恃势之刑）；丑戌未相刑（无恩之刑）；辰午酉亥自刑
XING = {"子":"卯","卯":"子",
        "寅":"巳","巳":"申","申":"寅",
        "丑":"戌","戌":"未","未":"丑",
        "辰":"辰","午":"午","酉":"酉","亥":"亥"}
HAI = {"申":"亥","亥":"申","子":"巳","巳":"子","寅":"亥","亥":"寅",
       "午":"巳","巳":"午","酉":"寅","寅":"酉","辰":"丑","丑":"辰","戌":"丑","丑":"戌","未":"戌","戌":"未"}

# 神煞映射
# 驿马律：申子辰马在寅，寅午戌马在申，巳酉丑马在亥，亥卯未马在巳
YIMA_MAP = {"申":"寅","子":"寅","辰":"寅",
            "寅":"申","午":"申","戌":"申",
            "巳":"亥","酉":"亥","丑":"亥",
            "亥":"巳","卯":"巳","未":"巳"}
# 华盖律：申子辰在辰，寅午戌在戌，巳酉丑在丑，亥卯未在未
HUAGAI_MAP = {"申":"辰","子":"辰","辰":"辰",
              "寅":"戌","午":"戌","戌":"戌",
              "巳":"丑","酉":"丑","丑":"丑",
              "亥":"未","卯":"未","未":"未"}
# 文昌（据《六壬大全》"甲巳乙午丙戊申，丁己酉庚亥辛子，壬寅癸卯"）
WENCHANG_MAP = {"甲":"巳","乙":"午","丙":"申","丁":"酉","戊":"申",
                "己":"酉","庚":"亥","辛":"子","壬":"寅","癸":"卯"}
# 劫煞律：申子辰在巳，寅午戌在亥，巳酉丑在寅，亥卯未在申
JIESHA_MAP = {"申":"巳","子":"巳","辰":"巳",
              "寅":"亥","午":"亥","戌":"亥",
              "巳":"寅","酉":"寅","丑":"寅",
              "亥":"申","卯":"申","未":"申"}
# 灾煞律：申子辰在午，寅午戌在子，巳酉丑在卯，亥卯未在酉
ZAISHA_MAP = {"申":"午","子":"午","辰":"午",
              "寅":"子","午":"子","戌":"子",
              "巳":"卯","酉":"卯","丑":"卯",
              "亥":"酉","卯":"酉","未":"酉"}

# 中气→月将映射（中气后启用对应月将）
# 据《六壬大全》：太阳过宫以中气为界，中气当日及之后用新将
# sanzhi.jieqi.ZHONGQI_YUEJIANG 权威版本（冬至=丑将起，按节气顺推一月）
YUE_JIANG_BY_JIEQI = {
    "冬至": "丑", "大寒": "子", "雨水": "亥", "春分": "戌",
    "谷雨": "酉", "小满": "申", "夏至": "未", "大暑": "午",
    "处暑": "巳", "秋分": "辰", "霜降": "卯", "小雪": "寅",
}
_ZHONG_QI_NAMES = frozenset(YUE_JIANG_BY_JIEQI.keys())

def get_yuejiang(year, month, day, hour=None, provider=None):
    """月将以中气定：找最近的前一中气，查表得月将

    规则：太阳过宫以中气为界，中气当日及之后使用新将，直到下一中气。
    例：处暑(8-23)后到秋分(9-23)前用巳将（处暑是中气，当日即切换）。
    例：小寒后，前一中气是大寒 → 用子将（小寒是节气非中气，不算换将节点）。
    """
    from datetime import date as _date, timedelta as _td
    from lunar_python import Solar as _Solar
    if provider is not None:
        try:
            # 路径1：从 provider 的 lunar_data 取前一中气
            l = getattr(provider, 'get_lunar_data', lambda *a,**k: None)(year, month, day, _hour12(hour))
            jq_name = getattr(l, 'prev_jieqi_name', None)
            jq_type = getattr(l, 'prev_jieqi_type', None)
            if jq_name and jq_name in _ZHONG_QI_NAMES and jq_type == "中":
                return YUE_JIANG_BY_JIEQI[jq_name]
            # 若前节气是节气（非中气），需找更前一个中气
            # 此处兜底用本地 fallback 逻辑
        except Exception:
            pass

    # 路径2：直接从 solar 计算——向前扫描最多 60 天找中气
    # ponytail: 原写法把 date/timedelta/calendar 三个 import 塞在循环里（反复 import，
    # 且 calendar 仅在负日兜底分支才用到、正常路径从不触发，属死代码）。
    # 现把 import 提到函数顶部，回退改用 date-timedelta 原生跨月处理，删除手工负日分支。
    base_dt = _date(year, month, day)
    for offset in range(60):
        dt = base_dt - _td(days=offset)
        ss = _Solar(dt.year, dt.month, dt.day, 12, 0, 0)
        ll = ss.getLunar()
        jq = ll.getPrevJieQi()
        jq_name = jq.getName() if hasattr(jq, 'getName') else ""
        # 中气判断：冬至/大寒/雨水/春分/谷雨/小满/夏至/大暑/处暑/秋分/霜降/小雪
        if jq_name in _ZHONG_QI_NAMES:
            return YUE_JIANG_BY_JIEQI[jq_name]
    # 兜底
    _FALLBACK = {"子":"子","丑":"丑","寅":"寅","卯":"卯","辰":"辰","巳":"巳",
                 "午":"午","未":"未","申":"申","酉":"酉","戌":"戌","亥":"亥"}
    return _FALLBACK.get(str(day % 12 or 12), "巳")

# 农历提供者（返回轻量命名空间对象，供本模块读取干支）
from lunar_python import Solar as _Solar
class DefaultLunarProvider:
    def get_lunar_data(self, year, month, day, hour):
        s = _Solar(year, month, day, _hour12(hour), 0, 0)
        l = s.getLunar()
        class _Data:
            pass
        d = _Data()
        d.ganzhi_day = l.getDayInGanZhi()
        d.ganzhi_time = l.getTimeInGanZhi()
        d.ganzhi_month = l.getMonthInGanZhi()
        d.ganzhi_year = l.getYearInGanZhi() if hasattr(l, 'getYearInGanZhi') else (l.getYear(), l.getMonth(), l.getDay())
        return d

# 传统天气占断（由 sanzhi.weather_traditional 统一提供，见下）
from sanzhi.weather_traditional import analyze_weather, TraditionalWeather

# ============================================================
# 大六壬专用常量（仅保留六壬特有，通用常量从 sanzhi 导入）
# ============================================================

# 贵人歌：日干 → (昼贵, 夜贵) ——据《六壬大全》卷一
GUI_REN = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("巳", "卯"), "癸": ("巳", "卯"),
    "辛": ("午", "寅"),
}

# 天将顺布顺序 ——据《六壬大全》卷一
TIAN_JIANG_SHUN = ["贵人", "腾蛇", "朱雀", "六合", "勾陈", "青龙", "天空", "白虎", "太常", "玄武", "太阴", "天后"]
# 天将逆布顺序
TIAN_JIANG_NI = ["贵人", "天后", "太阴", "玄武", "太常", "白虎", "天空", "青龙", "勾陈", "六合", "朱雀", "腾蛇"]

# 昼时支（卯辰巳午未申为昼）
DAY_BRANCHES = frozenset("卯辰巳午未申")

# 顺逆分界宫位（贵人所临地盘宫在亥子丑寅卯辰顺，巳午未申酉戌逆）
SHUN_POS = frozenset("亥子丑寅卯辰")
NI_POS = frozenset("巳午未申酉戌")

# 桃花（咸池）：申子辰在酉，寅午戌在卯，巳酉丑在午，亥卯未在子
TAOHUA_MAP = {
    "申": "酉", "子": "酉", "辰": "酉",
    "寅": "卯", "午": "卯", "戌": "卯",
    "巳": "午", "酉": "午", "丑": "午",
    "亥": "子", "卯": "子", "未": "子",
}

# 五合（天干五合：甲己、乙庚、丙辛、丁壬、戊癸）
WU_HE = {
    "甲": "己", "乙": "庚", "丙": "辛", "丁": "壬", "戊": "癸",
    "己": "甲", "庚": "乙", "辛": "丙", "壬": "丁", "癸": "戊",
}

# 三合同局下一位（阴日别责用）：取日支顺行第四位（同三合局循环的下一支）
# 注：并非"前一位"——数值为日支往后4步，落在同一三合局的下一支
#     （申子辰水/寅午戌火/巳酉丑金/亥卯未木 的循环）
SAN_HE_NEXT = {
    "申": "子", "子": "辰", "辰": "申",
    "寅": "午", "午": "戌", "戌": "寅",
    "巳": "酉", "酉": "丑", "丑": "巳",
    "亥": "卯", "卯": "未", "未": "亥",
}


def _sixty_idx(gan: str, zhi: str) -> int:
    """干支在六十甲子中的位置 (0-59)"""
    si = STEM_TO_IDX[gan]
    bi = BRANCH_TO_IDX[zhi]
    for i in range(si, 60, 10):
        if i % 12 == bi:
            return i
    return 0


def _make_dipan() -> dict:
    """地盘：十二地支按顺序固定"""
    return {b: b for b in EARTHLY_BRANCHES}


def _make_tianpan(yue_jiang: str, shi_zhi: str) -> dict:
    """天盘：月将加时支，顺行十二支（使用1-based索引计算偏移）"""
    # 使用1-based索引：子=1, 丑=2, ... 亥=12
    yj_idx = BRANCH_TO_IDX[yue_jiang] + 1
    sz_idx = BRANCH_TO_IDX[shi_zhi] + 1
    offset = (yj_idx - sz_idx) % 12
    return {b: EARTHLY_BRANCHES[(i + offset) % 12] for i, b in enumerate(EARTHLY_BRANCHES)}


# ============================================================
# 计算器
# ============================================================

class LiuRenCalculator:
    """大六壬排盘计算器
    
    核心流程：
    1. 获取农历干支（年月日时）——依据 lunar_python
    2. 定月将——据《六壬大全》首传法，以中气定太阳过宫
    3. 排地盘/天盘——月将加时支
    4. 排四课——干上、支上、日支上、日干上
    5. 九宗门判定链定三传——伏吟→贼克/比用/涉害→返吟→八专→别责→遥克→昴星
    6. 排天将——贵人顺逆布十二宫
    7. 查神煞——驿马、桃花、文昌、华盖、劫煞、灾煞、岁破、天乙贵人
    """

    def __init__(self, year: int, month: int, day: int, hour: int):
        self.year, self.month, self.day, self.hour = year, month, day, hour
        self._calc()

    def _calc(self):
        # ---- 农历/干支（委托 DefaultLunarProvider）----
        provider = DefaultLunarProvider()
        self.lunar_data = provider.get_lunar_data(self.year, self.month, self.day, self.hour)
        
        self.ri_gan = self.lunar_data.ganzhi_day[0]
        self.ri_zhi = self.lunar_data.ganzhi_day[1]
        self.shi_gan = self.lunar_data.ganzhi_time[0]
        self.shi_zhi = self.lunar_data.ganzhi_time[1]
        self.yue_zhi = self.lunar_data.ganzhi_month[1]
        self.nian_gan = self.lunar_data.ganzhi_year[0]
        self.nian_zhi = self.lunar_data.ganzhi_year[1]
        self.nian_gan_zhi = self.nian_gan + self.nian_zhi

        # 月将：以最近中气定太阳过宫
        self.yue_jiang = get_yuejiang(self.year, self.month, self.day, self.hour, provider)

        # 地盘/天盘
        self.dipan = _make_dipan()
        self.tianpan = _make_tianpan(self.yue_jiang, self.shi_zhi)

        # 四课
        self._make_si_ke()

        # 九宗门 + 三传
        self._make_san_chuan()

        # 空亡
        self.kong_wang = get_kong_wang(self.ri_gan, self.ri_zhi)

        # 天将
        self._make_tian_jiang()

        # 神煞
        self._make_shen_sha()

        # 天气（传统占断）
        self.weather = analyze_weather(
            "liuren",
            {"chart": {}},  # liuren 用不着 chart
            si_ke=self.si_ke,
            san_chuan=self.san_chuan,
            tian_jiang=self.tian_jiang_list,
            shen_sha=self.shen_sha,
            jieqi=self.lunar_data.prev_jieqi_name if hasattr(self.lunar_data, 'prev_jieqi_name') else ""
        ).to_dict()

    # ---- 四课 ----
    def _make_si_ke(self):
        """四课：第一课干上神、第二课支上神、第三课日支上神、第四课日干上神
        
        据《六壬大全》卷一首传法：
        - 第一课：日干寄宫（地盘）→ 天盘上神
        - 第二课：第一课上神再起（上上神）
        - 第三课：日支（地盘）→ 天盘上神
        - 第四课：第三课上神再起
        """
        gong = GAN_GONG[self.ri_gan]
        tp = self.tianpan
        # 第一课：日干寄宫（地盘）-> 天盘上神
        s1 = tp[gong]
        # 第二课：第一课上神再起（上上神）
        s2 = tp[s1]
        # 第三课：日支（地盘）-> 天盘上神
        s3 = tp[self.ri_zhi]
        # 第四课：第三课上神再起
        s4 = tp[s3]
        self.si_ke = [
            {"di": gong, "shang": s1, "name": "第一课"},
            {"di": s1, "shang": s2, "name": "第二课"},
            {"di": self.ri_zhi, "shang": s3, "name": "第三课"},
            {"di": s3, "shang": s4, "name": "第四课"},
        ]

    # ---- 九宗门 + 三传（按判定链）----
    def _make_san_chuan(self):
        """九宗门判定链：伏吟→贼克/比用/涉害→返吟→八专→别责→遙克→昴星
        
        据《六壬大全》卷一、《毕法赋》判定次序
        """
        yj = self.yue_jiang
        sz = self.shi_zhi
        dlog(f"开始九宗门判定: 月将={yj}, 时支={sz}")
        
        # 1. 伏吟：月将与占时同支
        if yj == sz:
            dlog("判定: 伏吟 (月将==时支)")
            self._fu_yin()
            return
        
        # 2. 返吟：月将与占时相冲（结构性判断，须先于贼克分流）
        # 注：返吟内部自行处理"有克则回落贼克、课体另记返吟"
        if (BRANCH_TO_IDX[yj] + 6) % 12 == BRANCH_TO_IDX[sz]:
            dlog("判定: 返吟 (月将与时支相冲)")
            self._fan_yin()
            return
        
        # 3. 八专：日干寄宫与日支同支，且四课无克
        if self._is_bazhuan():
            dlog("判定: 八专 (日干寄宫==日支 且 无克)")
            self._ba_zhuan()
            return
        
        # 4. 别责：四课去重后只剩三课，且无克，且非八专
        if self._is_bieze():
            dlog("判定: 别责 (四课去重=3 且 无克 且 非八专)")
            self._bie_ze()
            return
        
        # 5. 贼克/比用/涉害（核心判定链）
        if self._find_zei_ke():
            dlog("判定: 进入贼克/比用/涉害核心链")
            self._zei_ke_bi_yu_she_hai()
            return
        
        # 6. 遥克：四课齐备无克，不落上述各门
        dlog("判定: 进入遥克/昴星末端链")
        self._yao_ke()
        
        # 7. 昴星：判定链末端，恒有解
        if not hasattr(self, 'jiu_zong_men'):
            dlog("判定: 昴星 (判定链末端)")
            self._mao_xing()

    # --- 1. 伏吟 ---
    def _fu_yin(self):
        self.jiu_zong_men = "伏吟法"
        yang = self.ri_gan in "甲丙戊庚壬"
        if yang:
            c1 = self.si_ke[0]["shang"]
        else:
            c1 = self.si_ke[2]["shang"]
        # 中传：初传之刑
        c2 = XING.get(c1, c1)
        # 末传：中传之刑
        c3 = XING.get(c2, c2)
        # 自刑特殊处理
        if c1 in "辰午酉亥":
            if self.ri_gan in "甲丙戊庚壬":
                c2 = self.si_ke[2]["shang"]  # 阳日取支上神
            else:
                c2 = self.si_ke[0]["shang"]  # 阴日取干上神
            c3 = XING.get(c2, c2)
        self.san_chuan = {"chu": c1, "zhong": c2, "mo": c3}

    # --- 2. 返吟 ---
    def _fan_yin(self):
        # 检查四课是否有克
        candidates = self._find_zei_ke()
        if candidates:
            # 有克则回落贼克法
            self.jiu_zong_men = "返吟法(回落贼克)"
            self._resolve_zei_ke(candidates)
            return
        # 无克：取日支驿马为初传，支上神为中传，干上神为末传
        self.jiu_zong_men = "返吟法"
        c1 = YIMA_MAP.get(self.ri_zhi, self.ri_zhi)
        # 支上神 = 天盘上日支上神
        c2 = self.tianpan.get(self.ri_zhi, "")
        c3 = self.tianpan.get(GAN_GONG[self.ri_gan], "")
        self.san_chuan = {"chu": c1, "zhong": c2, "mo": c3}

    # --- 3. 八专 ---
    def _is_bazhuan(self) -> bool:
        # 日干寄宫与日支同支，且四课无克
        return GAN_GONG[self.ri_gan] == self.ri_zhi and not self._find_zei_ke()

    def _ba_zhuan(self):
        """八专法取三传

        口诀（《六壬视斯》）："两课无克号八专，阳日时神顺行三。
        阴日阴神逆三数，中末都来干上眠。"

        - 阳日：以【第一课上神】为起点，于**天盘顺数三位**（含起点）为初传
        - 阴日：以【第四课上神】为起点，于**天盘逆数三位**（含起点）为初传
        - 中传、末传俱取干上神

        旧实现直接令 初传 = 第一课/第四课上神（未依口诀数三神），
        且阴日取第四课上神却未逆数，属错取。今按口诀补全。
        """
        self.jiu_zong_men = "八专法"
        gan_shang = self.tianpan.get(GAN_GONG[self.ri_gan], "")

        if self.ri_gan in "甲丙戊庚壬":          # 阳日（刚日）
            start = self.si_ke[0]["shang"]      # 第一课上神（干上神）
            c1 = self._shu_san_shen(start, forward=True)
        else:                                    # 阴日（柔日）
            start = self.si_ke[3]["shang"]      # 第四课上神
            c1 = self._shu_san_shen(start, forward=False)

        self.san_chuan = {"chu": c1, "zhong": gan_shang, "mo": gan_shang}

    def _shu_san_shen(self, start: str, forward: bool) -> str:
        """于天盘自 start 数三神（含起点），返回末位之神

        八专法"顺行三/逆三数"即此。若天盘缺该支则退回本地支（防御）。
        """
        if start not in self.tianpan:
            return start
        # 天盘映射：地盘支 -> 天盘支；先取反查（天盘支 -> 所临地盘支）
        inv = {v: k for k, v in self.tianpan.items()}
        cur = start
        for _ in range(2):                       # 再数两步，共三神
            di = inv.get(cur)                    # 该天盘神所临之地盘支
            if di is None:
                break
            idx = (BRANCH_TO_IDX[di] + (1 if forward else -1)) % 12
            cur = self.tianpan[EARTHLY_BRANCHES[idx]]
        return cur

    # --- 4. 别责 ---
    def _is_bieze(self) -> bool:
        # 别责：四课退化为三课（有一课上下神相同，课程去重=3），且无克，且非八专日。
        # 根因（2026-10-11 修复）：旧判据把「上下神两个格位」合并进同一集合去重
        # （8 格位去重==3）。但第 1/2 课、第 3/4 课首尾相接（前课上神=后课下神），
        # 独立支上限仅 6，格位去重==3 数学上不可能达成 → 别责法恒不触发（死分支）。
        # 正确判据：课程（di,shang 对）去重==3 ⇔ 恰有一课上下神相同。
        courses = {(ke["di"], ke["shang"]) for ke in self.si_ke}
        return (len(courses) == 3
                and not self._find_zei_ke()
                and not self._is_bazhuan())

    def _bie_ze(self):
        self.jiu_zong_men = "别责法"
        if self.ri_gan in "甲丙戊庚壬":  # 阳日
            # 取日干之五合干的寄宫，再取该宫上神
            he_gan = WU_HE.get(self.ri_gan, self.ri_gan)
            gong = GAN_GONG.get(he_gan, "")
            c1 = self.tianpan.get(gong, "")
        else:
            # 阴日取日支三合局中的顺行第四位（同局下一位，日支往后4步）
            c1 = SAN_HE_NEXT.get(self.ri_zhi, self.ri_zhi)
        self.san_chuan = {
            "chu": c1,
            "zhong": self.tianpan.get(GAN_GONG[self.ri_gan], ""),
            "mo": self.tianpan.get(GAN_GONG[self.ri_gan], ""),
        }

    # --- 5. 贼克/比用/涉害核心链 ---
    def _zei_ke_bi_yu_she_hai(self):
        candidates = self._find_zei_ke()
        
        if not candidates:
            return  # 无克，留给遥克/昴星
        
        if len(candidates) == 1:
            self.jiu_zong_men = "贼克法"
            self._resolve_zei_ke(candidates)
            return
        
        # 多于一课贼克 -> 比用法
        gan_yy = STEM_TO_IDX[self.ri_gan] % 2  # 0=阳, 1=阴
        bi = [c for c in candidates if BRANCH_TO_IDX[c["shang"]] % 2 == gan_yy]
        if len(bi) == 1:
            self.jiu_zong_men = "比用法"
            self._resolve_zei_ke(bi)
            return
        elif len(bi) > 1:
            self.jiu_zong_men = "涉害法"
            candidates = self._she_hai(bi)
            self._resolve_zei_ke(candidates)
            return
        else:
            # 比用无人，回贼克
            self.jiu_zong_men = "贼克法"
            self._resolve_zei_ke(candidates)
            return

    def _find_zei_ke(self) -> list:
        """找出四课中五行相克的课：下贼上（下克上）优先于上克下
        
        据《六壬大全》卷一"下贼上"优先原则
        """
        result = []
        for i, ke in enumerate(self.si_ke):
            e_s = ELEMENT_MAP.get(ke["shang"], "")  # 上神五行
            e_d = ELEMENT_MAP.get(ke["di"], "")      # 下神五行
            rel_down = get_relation(e_d, e_s)  # 下神对上神的关系
            rel_up = get_relation(e_s, e_d)    # 上神对下神的关系
            if rel_down == "克":      # 下贼上：下神克上神
                result.append({"shang": ke["shang"], "di": ke["di"], "idx": i, "type": "下贼上"})
            elif rel_up == "克":      # 上克下
                result.append({"shang": ke["shang"], "di": ke["di"], "idx": i, "type": "上克下"})
        # 下贼上优先
        xia_ke = [c for c in result if c["type"] == "下贼上"]
        if xia_ke:
            return xia_ke
        return result

    def _resolve_zei_ke(self, candidates):
        """确定三传"""
        # 取最早（按课序）的一课上神为初传
        c1 = candidates[0]["shang"]
        # 中传：初传之上神（天盘初传所对应的地盘再取天盘）
        c2 = self._get_shang(c1)
        # 末传：中传之上神
        c3 = self._get_shang(c2)
        self.san_chuan = {"chu": c1, "zhong": c2, "mo": c3}

    def _get_shang(self, zhi: str) -> str:
        """给定地支（地盘），返回其在天盘上的上神"""
        return self.tianpan.get(zhi, "")

    def _she_hai(self, candidates: list) -> list:
        """涉害法：数深浅（历经地支克我者个数），深者发用；相等取四孟/四仲/四季

        规则（据《六壬大全》卷一、本站《毕法赋》注解）：
        - 候选上神自地盘本家(上神固定宫位)顺行至所临之宫(四课di)
        - 路上历过的地盘支中克上神者的个数，多者为深，深者发用
        - 深浅相等取四仲>四孟>四季（本站规则，注：部分流派主张四孟>四仲）
        """
        best_cnt = -1
        best = []
        for c in candidates:
            shang = c["shang"]
            e_shang = ELEMENT_MAP[shang]
            # 所临之宫 = 四课中的 di
            target_idx = BRANCH_TO_IDX[c["di"]]
            # 上神本家 = 上神在固定地盘的位置（子在子宫、丑在丑宫...）
            start_idx = BRANCH_TO_IDX[shang]
            cnt = 0
            i = start_idx
            while True:
                i = (i + 1) % 12
                if i == target_idx:
                    break
                b = EARTHLY_BRANCHES[i]
                if get_relation(ELEMENT_MAP.get(b, ""), e_shang) == "克":
                    cnt += 1
            if cnt > best_cnt:
                best_cnt = cnt
                best = [c]
            elif cnt == best_cnt:
                best.append(c)
        # 深浅相等：据《六壬大全》主流 四孟(寅申巳亥) > 四仲(子午卯酉) > 四季(辰戌丑未)
        si_ji = {"辰", "戌", "丑", "未"}
        meng = {"寅", "申", "巳", "亥"}
        zhong = {"子", "午", "卯", "酉"}
        # 优先四孟
        meng_c = [c for c in best if c["shang"] in meng]
        if meng_c:
            return [min(meng_c, key=lambda x: x["idx"])]
        # 其次四仲
        zhong_c = [c for c in best if c["shang"] in zhong]
        if zhong_c:
            return [min(zhong_c, key=lambda x: x["idx"])]
        # 最后四季
        si_ji_c = [c for c in best if c["shang"] in si_ji]
        if si_ji_c:
            return [min(si_ji_c, key=lambda x: x["idx"])]
        best.sort(key=lambda x: x["idx"])
        return [best[0]]

    # --- 6. 遥克 ---
    def _yao_ke(self):
        """遥克法：蒿矢（上神遥克日干）优先于弹射（日干遥克上神）

        口诀："先取神遥来克日，无神克与日相交。"
              "复有两神来克日，或有日去克两神，当择与日干比者用，
               阳日用阳、阴用阴。"
        多候选时：先取与日干阴阳相同者（比用）；仍不止一个或无一比，
        则回涉害决之（与 references/jiu-zong-men.md 一致）。
        """
        self.jiu_zong_men = "遥克法"
        gan_yy = STEM_TO_IDX[self.ri_gan] % 2      # 0=阳 1=阴

        def cands_of(up_ke: bool):
            """up_ke=True 取上神克日干（蒿矢），否则取日干克上神（弹射）

            统一构造带 idx/type 的候选，以复用 _she_hai（其依赖 idx）。
            """
            out = []
            for i, ke in enumerate(self.si_ke):
                e_s = ELEMENT_MAP.get(ke["shang"], "")
                e_g = ELEMENT_MAP[self.ri_gan]
                if not e_s:
                    continue
                rel = (get_relation(e_s, e_g) == "克") if up_ke else (get_relation(e_g, e_s) == "克")
                if rel:
                    out.append({"shang": ke["shang"], "di": ke["di"], "idx": i,
                                "type": "蒿矢" if up_ke else "弹射"})
            return out

        def pick(cands):
            if not cands:
                return None
            if len(cands) == 1:
                return cands[0]
            bi = [c for c in cands if BRANCH_TO_IDX[c["shang"]] % 2 == gan_yy]
            if len(bi) == 1:
                return bi[0]
            return self._she_hai(bi if bi else cands)[0]   # 涉害决之

        for up in (True, False):                   # 1. 蒿矢  2. 弹射
            hit = pick(cands_of(up))
            if hit:
                self._resolve_zei_ke([hit])
                return

        # 3. 还取不出 -> 昴星
        self._mao_xing()

    # --- 7. 昴星 ---
    def _mao_xing(self):
        self.jiu_zong_men = "昴星法"
        # 阳日取地盘酉宫之上的天盘神为初传
        if self.ri_gan in "甲丙戊庚壬":  # 阳日
            c1 = self.tianpan.get("酉", "")
            c2 = self.tianpan.get(self.ri_zhi, "")  # 中传取支上神
            c3 = self.tianpan.get(GAN_GONG[self.ri_gan], "")  # 末传取干上神
        else:  # 阴日
            # 阴日取天盘酉所临的地盘神为初传
            # 即天盘上酉所对应的地盘支
            di_of_you = None
            for di, shang in self.tianpan.items():
                if shang == "酉":
                    di_of_you = di
                    break
            c1 = di_of_you or "酉"
            c2 = self.tianpan.get(GAN_GONG[self.ri_gan], "")  # 中传取干上神
            c3 = self.tianpan.get(self.ri_zhi, "")  # 末传取支上神
        self.san_chuan = {"chu": c1, "zhong": c2, "mo": c3}

    # ---- 天将 ---
    def _make_tian_jiang(self):
        is_day = self.shi_zhi in DAY_BRANCHES
        gui_zhi = GUI_REN[self.ri_gan][0 if is_day else 1]

        # 贵人所临地盘宫
        gui_di = None
        for b in EARTHLY_BRANCHES:
            if self.tianpan[b] == gui_zhi:
                gui_di = b
                break

        if gui_di in SHUN_POS:
            order, step = TIAN_JIANG_SHUN, 1
        else:
            order, step = TIAN_JIANG_NI, -1

        gui_idx = BRANCH_TO_IDX[gui_zhi]
        self.tian_jiang_list = []
        for i, jiang in enumerate(order):
            zhi = EARTHLY_BRANCHES[(gui_idx + i * step) % 12]
            self.tian_jiang_list.append({"jiang": jiang, "zhi": zhi})

    # ---- 神煞 ---
    def _make_shen_sha(self):
        self.shen_sha = {}
        # 驿马
        self.shen_sha["驿马"] = YIMA_MAP.get(self.ri_zhi, self.ri_zhi)
        # 桃花
        self.shen_sha["桃花"] = TAOHUA_MAP.get(self.ri_zhi, "")
        # 文昌
        self.shen_sha["文昌"] = WENCHANG_MAP.get(self.ri_gan, self.ri_gan)
        # 华盖（按日支查）
        self.shen_sha["华盖"] = HUAGAI_MAP.get(self.ri_zhi, self.ri_zhi)
        # 劫煞（按日支查）
        self.shen_sha["劫煞"] = JIESHA_MAP.get(self.ri_zhi, self.ri_zhi)
        # 灾煞（按日支查）
        self.shen_sha["灾煞"] = ZAISHA_MAP.get(self.ri_zhi, self.ri_zhi)
        # 岁破
        self.shen_sha["岁破"] = LIU_CHONG.get(self.nian_zhi, self.nian_zhi)
        # 天乙贵人
        is_day = self.shi_zhi in DAY_BRANCHES
        self.shen_sha["天乙贵人"] = GUI_REN[self.ri_gan][0 if is_day else 1]

    def to_dict(self) -> dict:
        return {
            "si_ke": self.si_ke,
            "jiu_zong_men": self.jiu_zong_men,
            "san_chuan": self.san_chuan,
            "yue_jiang": self.yue_jiang,
            "kong_wang": self.kong_wang,
            "tian_jiang": self.tian_jiang_list,
            "ri_gan_zhi": self.ri_gan + self.ri_zhi,
            "nian_gan_zhi": self.nian_gan_zhi,
            "shen_sha": self.shen_sha,
            "yima": YIMA_MAP.get(self.ri_zhi, self.ri_zhi),
            "wenchang": WENCHANG_MAP.get(self.ri_gan, self.ri_gan),
            "huagai": HUAGAI_MAP.get(self.ri_zhi, self.ri_zhi),
            "jiesha": JIESHA_MAP.get(self.ri_zhi, self.ri_zhi),
            "zaisha": ZAISHA_MAP.get(self.ri_zhi, self.ri_zhi),
            "suipo": LIU_CHONG.get(self.nian_zhi, self.nian_zhi),
            "weather": self.weather,
        }

    def to_text(self) -> str:
        d = self.to_dict()
        L = []
        L.append("=" * 60)
        L.append("🔮 大六壬排盘（据《六壬大全》首传法）")
        L.append("=" * 60)
        L.append(f"年柱：{d['nian_gan_zhi']}  日柱：{d['ri_gan_zhi']}  月将：{d['yue_jiang']}  时辰：{self.shi_zhi}时（{self.hour:02d}点）")
        L.append(f"空亡：{'、'.join(d['kong_wang'])}")
        L.append("")
        L.append("📋 四课：")
        for ke in d["si_ke"]:
            L.append(f"  {ke['name']}：{ke['di']}上 {ke['shang']}")
        L.append("")
        L.append(f"⚖️ 九宗门：{d['jiu_zong_men']}")
        L.append(f"📊 三传：初传{d['san_chuan']['chu']} 中传{d['san_chuan']['zhong']} 末传{d['san_chuan']['mo']}")
        L.append("")
        L.append("🌟 十二天将：")
        for t in d["tian_jiang"]:
            L.append(f"  {t['jiang']}：{t['zhi']}")
        L.append("")
        L.append("🕉️ 核心神煞：")
        for name, pos in d["shen_sha"].items():
            if pos:
                L.append(f"  {name}：{pos}")
        L.append("=" * 60)
        return "\n".join(L)


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="大六壬排盘系统")
    parser.add_argument("-q", "--question", default="", help="求测问题")
    parser.add_argument("-y", "--year", type=int, default=None, help="年")
    parser.add_argument("-m", "--month", type=int, default=None, help="月")
    parser.add_argument("-d", "--day", type=int, default=None, help="日")
    # default=None：区分「未指定」与「指定为 0 点（子时）」
    # 旧写法 default=0 + `if args.hour > 0` 会把 -H 0 静默替换成当前小时。
    parser.add_argument("-H", "--hour", type=int, default=None, help="时（0-23）")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()
    now = local_now()
    c = LiuRenCalculator(
        args.year or now.year,
        args.month or now.month,
        args.day or now.day,
        args.hour if args.hour is not None else now.hour,
    )
    if args.json:
        print(json.dumps(c.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(c.to_text())


if __name__ == "__main__":
    main()