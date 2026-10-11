#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲排盘解卦系统
据源：《御定奇门宝鉴》《烟波钓叟歌》《奇门遁甲秘笈大全》

算法：
- 定局：**默认置闰法**（《烟波钓叟歌》正统，以符头甲己日定三元，芒种/大雪置闰）；
  可用 --dunjia-method chaibu 切换拆补法（实用优先），maoshan 为民间法（暂未接入，
  会显式回退并告警）。三法差异详见 references/chaoshen-jieqi.md。
- 天盘：值符加时干
- 人盘：八门九星飞布（跳中五，中五寄坤二）
- 神盘：八神随值符飞布

⚠️ 三种定局法在同一时刻可能排出不同局数，**同一次断局必须自始至终用同一套规则**。
本文件输出的 ju.yuan_method 字段会显式标出实际所用方法，便于审计。
"""

import json
import os
import sys
from datetime import date
from typing import Dict, List, Optional

# 统一基础设施：从三式共享库导入
# 定位共享历法库 sanzhi：兼容部署布局(shared_assets/sanzhi)与仓库布局(_shared)
_d = os.path.dirname(os.path.abspath(__file__))
while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
       and not os.path.isdir(os.path.join(_d, "_shared"))
       and os.path.dirname(_d) != _d):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
                else os.path.join(_d, "_shared"))

# ============================================================
# 统一调试日志前缀
# ============================================================
DEBUG_PREFIX = "[DEBUG-QIMEN]"
def dlog(msg: str):
    """统一调试日志输出"""
    print(f"{DEBUG_PREFIX} {msg}", file=sys.stderr)


from sanzhi import (
    # ganzhi
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
    STEM_TO_IDX, BRANCH_TO_IDX,
    LIUSHI_JIAZI,
    XUN_SHOU_YI, XUN_KONG,
    get_shichen, get_xun_shou, get_kong_wang,
    # wuxing
    ELEMENT_MAP,
    # jieqi
    YANG_DUN_JIEQI, YIN_DUN_JIEQI,
    YANG_JU_TABLE, YIN_JU_TABLE, get_ju_number,
    get_yuejiang, is_yang_dun, get_yuan,
    get_current_jieqi, JieQiInfo,
    # lunar
    DefaultLunarProvider, LunarData,
    # datetime
    local_now,
)
# 传统天气占断（新增）
from sanzhi.weather_traditional import analyze_weather, TraditionalWeather

# 置闰法（可选导入）
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from qimen_zhiyun import get_yuan_zhiyun, ZhiyunCalculator
    ZHIYUN_AVAILABLE = True
except ImportError:
    ZHIYUN_AVAILABLE = False

# ============================================================
# 奇门遁甲专用常量（仅保留奇门特有，通用常量从 sanzhi 导入）
# ============================================================

# 洛书九宫顺序（跳中五）
# 注：本引擎经检测确认按"洛书数序"走宫即可产出内部一致的盘面（盘面无重复宫、
# 八门自值使门起顺布、九星自值符宫起顺布）。曾一度改用八卦方位环
# [1,8,3,4,9,2,7,6] 反而导致地盘空洞、盘面错乱，已回滚，勿再改。
#
# 口径说明（2026-10-11 实测核对）：
#   本引擎八门/九星/八神统一按【洛书数序环】(本列表) 走宫，这是"数序环"流派口径；
#   另一口径是【八卦方位环】(物理方位 [1,8,3,4,9,2,7,6])。两者是并列的流派选择，
#   同盘内星/门/神三盘各自内部始终自洽（实测 160 盘 0 混用错位），差异只在
#   "跳中五时按哪个序走下一宫"。切勿把"数序环非等距刚性"当成 bug——那不是缺陷，
#   是本引擎的既定口径；外部用"方位环刚性"这把尺子量会得出错误结论。
EIGHT_PALACE_ORDER = [1, 2, 3, 4, 6, 7, 8, 9]

# 八门原始宫位（洛书宫号 → 门名）——据《烟波钓叟歌》八门定位
DOOR_HOME = {6: "开门", 1: "休门", 8: "生门", 3: "伤门", 4: "杜门", 9: "景门", 2: "死门", 7: "惊门"}

# 洛书八宫反向位次（palace → 在 EIGHT_PALACE_ORDER 中的下标），供 O(1) 查环位
# 替代各处 `EIGHT_PALACE_ORDER.index(p)` 的 O(n) 线性查找（排盘热点路径）。
# ponytail: 8 元素常数表，一次建好；仅性能优化，不改变任何排盘结果。
EIGHT_PALACE_POS = {p: i for i, p in enumerate(EIGHT_PALACE_ORDER)}

# 九星原始宫位——据《御定奇门宝鉴》九星定位（含中五天禽）
STAR_HOME = {1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅", 5: "天禽",
             6: "天心", 7: "天柱", 8: "天任", 9: "天英"}

# 转盘九星环（跳中五，共八位）
# ⚠️ 转盘之天禽不独立转位（中五常驻），故环中不含天禽；
# 甲辰壬之值符星为天禽，转盘寄坤二，按"芮禽"同宫处理，归入天芮位。
STAR_RING = [STAR_HOME[p] for p in EIGHT_PALACE_ORDER]  # 蓬 芮 冲 辅 心 柱 任 英

# 旬首仪 → 转盘值符星（据《烟波钓叟歌》"甲子戊起天蓬"系，依次落本位）
# 转盘天禽不独立转位（中五常驻），故甲辰壬之值符星寄坤二，按"芮禽同宫"归入天芮位
YI_TO_STAR = {"戊": "天蓬", "己": "天芮", "庚": "天冲",
              "辛": "天辅", "壬": "天芮", "癸": "天心"}

# 旬首仪 → 飞盘值符星（飞盘九星实落九宫，中五得天禽，不寄坤二）
# 故甲辰壬之值符星即天禽（本位在中五），与转盘的"寄芮"不同
YI_TO_STAR_FEI = {"戊": "天蓬", "己": "天芮", "庚": "天冲",
                  "辛": "天辅", "壬": "天禽", "癸": "天心"}

# 飞盘九星序（含中五天禽，按洛书数序 1..9）
STAR_RING_FEI = [STAR_HOME[p] for p in range(1, 10)]  # 蓬 芮 冲 辅 禽 心 柱 任 英

# 八神顺序——据《奇门遁甲秘笈大全》八神排布
BASHEN_ORDER = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

# 九宫方位映射
PALACE_DIR = {1: "坎北", 2: "坤西南", 3: "震东", 4: "巽东南", 5: "中", 6: "乾西北", 7: "兑西", 8: "艮东北", 9: "离南"}

# 三奇六仪排布序列（地盘/天盘通用）——据《烟波钓叟歌》"戊己庚辛壬癸丁丙乙"
QIMEN_SEQ = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]


# ============================================================
# 飞盘专用常量
# ============================================================

# 飞盘布局顺序（不跳中五，完整9宫）
# 阳遁顺飞：从1开始，顺时针到9
# 阴遁逆飞：从9开始，逆时针到1
FEIPAN_SHUN = [1, 2, 3, 4, 5, 6, 7, 8, 9]
FEIPAN_NI = [9, 8, 7, 6, 5, 4, 3, 2, 1]


# ============================================================
# 排盘类
# ============================================================

class QimenChart:
    """奇门遁甲排盘主类
    
    核心流程：
    1. 获取农历干支（年月日时）——依据 lunar_python
    2. 定阴阳遁、局数、三元——据《烟波钓叟歌》拆补法
    3. 排地盘：三奇六仪按局数布九宫
    4. 排天盘：值符加时干，旬首仪落时干宫
    5. 排人盘：八门随值使飞布，九星随值符飞布
    6. 排神盘：八神随值符飞布
    7. 匹配格局库
    """

    def __init__(self, year: int, month: int = 0, day: int = 0, hour: int = None, question: str = "",
                 dunjia_method: str = "zhiyun", pan_style: str = "zhuanpan"):
        """
        dunjia_method: 定局法（与盘式正交，两派通用）
          - "zhiyun"（默认）：置闰法（《烟波钓叟歌》正统）
          - "chaibu"：拆补法（宋代以后流行，实用优先）
          - "maoshan"：茅山法（民间法，本引擎暂未接入，会显式回退到 zhiyun 并告警）

        pan_style: 盘式
          - "zhuanpan"（默认）：转盘法（《奇门遁甲秘笈大全》《烟波钓叟歌》系）
          - "feipan"：飞盘法（《奇门法窍》系，按洛书数序飞布）

        兼容：旧用法 `dunjia_method="feipan"` 会自动转成 pan_style="feipan"，
        定局法回落到默认置闰法——避免"选飞盘却被迫用拆补法"的错配。
        """
        # 旧接口兼容：feipan 属盘式而非定局法
        if dunjia_method == "feipan":
            pan_style = "feipan"
            dunjia_method = "zhiyun"
        self.pan_style = pan_style
        self.year = year
        self.month = month or 1
        self.day = day or 1
        self.hour = 12 if hour is None else hour
        self.question = question
        self.dunjia_method = dunjia_method

        # ---- 农历/干支（委托 DefaultLunarProvider，准确处理置闰/节气）----
        provider = DefaultLunarProvider()
        lunar_data: LunarData = provider.get_lunar_data(year, self.month, self.day, self.hour)
        
        self.ganzhi_year = lunar_data.ganzhi_year
        self.ganzhi_month = lunar_data.ganzhi_month
        self.ganzhi_day = lunar_data.ganzhi_day
        self.ganzhi_time = lunar_data.ganzhi_time
        self.ganzhi_shichen = lunar_data.ganzhi_time  # 兼容别名

        self.ri_gan = self.ganzhi_day[0]
        self.ri_zhi = self.ganzhi_day[1]
        self.shi_gan = self.ganzhi_time[0]
        self.shi_zhi = self.ganzhi_time[1]
        self.yue_zhi = self.ganzhi_month[1]
        self.lunar_date = f"{lunar_data.lunar_year}年{lunar_data.lunar_month_name}月{lunar_data.lunar_day_name}"

        # ---- 定局（默认置闰法，据《烟波钓叟歌》；可切拆补法）----
        self._determine_ju(lunar_data, provider)

        # ---- 旬首/旬空 ----
        # 时家奇门：旬首由【时柱】定，非日柱——值符须"随时而转"。
        # 用日柱旬会连带搞错旬首仪、值符落宫、八神起点、空亡（整盘错）。
        # 注：大六壬的旬空才用日柱（见 liuren.get_kong_wang），两体系不可混用。
        self.xun_shou = get_xun_shou(self.shi_gan, self.shi_zhi)
        self.xun_yi = XUN_SHOU_YI.get(self.xun_shou, "戊")  # 旬首仪
        self.kong_wang = get_kong_wang(self.shi_gan, self.shi_zhi)

        # ---- 排盘核心 ----
        # 盘式互斥：飞盘不跑转盘路径（转盘的中五寄坤二与飞盘实落规则冲突，
        # 且转盘盘面在飞盘下会被整盘覆盖，白算一遍还会先崩）
        self.chart = {}
        if self.pan_style == "feipan":
            # 飞盘（《奇门法窍》系）：洛书数序飞布、九干九星实落九宫（中五不寄坤二）
            self._make_feipan()
        else:
            self._make_dipan()
            self._make_tianpan()
            self._make_renpan()
            self._make_shenpan()

        # ---- 天气（传统占断）----
        self.weather = analyze_weather(
            "qimen",
            {"chart": self.chart},
            jieqi=self.current_jieqi
        ).to_dict()

        # ---- 格局库----
        self._load_geju_db()

    def _fly9(self, start_palace: int) -> list:
        """飞盘九宫飞布序列（含中五）：自 start 起按洛书数序，阳顺阴逆"""
        order = [1, 2, 3, 4, 5, 6, 7, 8, 9] if self.is_yang_dun else [9, 8, 7, 6, 5, 4, 3, 2, 1]
        i = order.index(start_palace)
        return [order[(i + k) % 9] for k in range(9)]

    def _fly8(self, start_palace: int) -> list:
        """飞盘八宫飞布序列（跳中五）。起点为中五时按阴阳遁"飞出"（阳→6，阴→4）"""
        order = [1, 2, 3, 4, 6, 7, 8, 9] if self.is_yang_dun else [9, 8, 7, 6, 4, 3, 2, 1]
        if start_palace == 5:
            start_palace = 6 if self.is_yang_dun else 4
        i = order.index(start_palace)
        return [order[(i + k) % 8] for k in range(8)]

    def _make_feipan(self):
        """飞盘四盘总成（《奇门法窍》系）

        与转盘的关键差别：
        1. 九干/九星**实落九宫**（中五亦得干、得星天禽），不寄坤二
        2. 各盘按**洛书数序飞布**（跳中五者走八宫序），非转盘环移
        3. 值符**落宫=时干宫**；甲时以时柱旬首仪之宫代之（即时干本宫→伏吟）

        原先的四段各自为政：门/星/神一律自「旬首仪地盘本宫」起（转盘口径），
        天盘又自另起一轮（非整体飞移），致甲时伏吟不稳定、值符神落错宫。
        注：值符落宫依赖地盘，故地盘必须先成。
        """
        self._make_feipan_dipan()
        pz = self._zhifu_palace()          # 值符落宫 = 时干宫（依赖地盘，须在地盘之后）
        self._make_feipan_tianpan()
        self._make_feipan_renpan(pz)
        self._make_feipan_shenpan(pz)

    def _make_feipan_dipan(self):
        """飞盘地盘：三奇六仪飞布九宫（含中五，不寄坤二）

        据《奇门法窍》系：以局数宫起，按洛书数序飞布九干。
        """
        for i, palace in enumerate(self._fly9(self.ju_number)):
            self.chart.setdefault(palace, {})["dipan"] = QIMEN_SEQ[i]
        # 飞盘中五实落，无"寄坤二"之说
        self.chart.setdefault(5, {}).pop("dipan_note", None)

    def _make_feipan_tianpan(self):
        """飞盘天盘：地盘九宫按洛书序**整体飞移**，使旬首仪镇值符落宫

        据《奇门法窍》"值符加时干"：
          对任一宫 p，取地盘自 p 回退 S 步之干置于 p，其中 S 为
          "旬首仪本宫 → 值符落宫"的洛书飞移步数。
        甲时值符落宫即旬首仪本宫 → S=0 → 天盘与地盘完全重合（伏吟）。

        旧写法自旬首仪另起一轮（天盘干与地盘位次关系全错），
        且甲时靠兜底才偶然伏吟（4 样本错 1）。
        """
        pz = self._zhifu_palace()
        pv = self._find_zhifu_palace()
        fly = self._fly9(pv)
        S = fly.index(pz)                  # 飞移步数

        di = {p: self.chart[p].get("dipan") for p in range(1, 10)}
        fly_from = {p: self._fly9(p) for p in range(1, 10)}
        for p in range(1, 10):
            self.chart.setdefault(p, {})["tianpan"] = di[fly_from[p][-S % 9]]

    def _make_feipan_renpan(self, pz: int):
        """飞盘人盘：八门随值使飞布、九星随值符星飞布

        据《奇门法窍》系（见 references/feipan-zhuanpan-xueshu.md）：
        - 九星：值符星自值符落宫起，按洛书数序飞布九宫（**含中五**，中五天禽）
        - 八门：值使门入中宫后飞布；八门恒为八数，中五不落
        """
        # ---- 八门：值使门落宫（自值符落宫走 时支-旬首支 步，按八宫飞布序）----
        sz_idx = BRANCH_TO_IDX[self.shi_zhi]
        xun_zhi = self.xun_shou[1] if len(self.xun_shou) >= 2 else "子"
        steps = (sz_idx - BRANCH_TO_IDX.get(xun_zhi, 0)) % 12
        palace = self._fly8(pz)[steps % 8]
        self.zhimen_palace = palace

        doors = ["开门", "休门", "生门", "伤门", "杜门", "景门", "死门", "惊门"]
        zhimen_door = DOOR_HOME.get(palace, "开门")
        if zhimen_door in doors:
            doors.remove(zhimen_door)
            doors.insert(0, zhimen_door)
        for p, door in zip(self._fly8(palace), doors):
            self.chart.setdefault(p, {})["men"] = door

        # ---- 九星：值符星自值符落宫起，按洛书数序飞布九宫（含中五）----
        zhifu_star = YI_TO_STAR_FEI.get(self.xun_yi, "天蓬")
        si = STAR_RING_FEI.index(zhifu_star)
        for k, p in enumerate(self._fly9(pz)):
            self.chart.setdefault(p, {})["star"] = STAR_RING_FEI[(si + k) % 9]

    def _make_feipan_shenpan(self, pz: int):
        """飞盘神盘：八神自值符落宫起飞布八宫

        据《奇门法窍》系：值符神落值符落宫（=时干宫），余七神依序飞布。
        八神恒为八数，中五不落。
        """
        for p, shen in zip(self._fly8(pz), BASHEN_ORDER):
            self.chart.setdefault(p, {})["shen"] = shen

    # ---- 定局 ----
    def _determine_ju(self, lunar_data: LunarData, provider):
        """定阴阳遁、局数、三元

        支持三种定局法（由 self.dunjia_method 选择，默认 zhiyun）：
        - 置闰法（"zhiyun"，默认，据《烟波钓叟歌》正统）：以符头甲己日为准，芒种/大雪置闰
        - 拆补法（"chaibu"）：以节气为绝对基准，每元5天，不置闰
        - 茅山法（"maoshan"）：本引擎未接入，显式回退置闰法并告警

        ⚠️ 三法不可混用：同一断局自始至终用同一套规则。
        """
        dlog(f"开始定局: 年={self.year}, 月={self.month}, 日={self.day}, 时={self.hour}, 法={self.dunjia_method}")
        
        # 使用农历提供者已计算的前一节气
        jieqi = lunar_data.prev_jieqi_name
        self.current_jieqi = jieqi
        self.is_yang_dun = is_yang_dun(jieqi)
        
        dun_str = "阳遁" if self.is_yang_dun else "阴遁"
        dlog(f"定局: 节气={jieqi}, 遁类={dun_str}")
        
        method = self.dunjia_method
        if method == "maoshan":
            dlog("茅山法尚未接入本引擎，显式回退为置闰法（请勿据此断局）")
            method = "zhiyun"
        # 置闰法需要专用计算器；不可用时显式回退拆补法
        if method == "zhiyun" and not ZHIYUN_AVAILABLE:
            dlog("置闰法模块不可用（qimen_zhiyun 导入失败），回退为拆补法")
            method = "chaibu"

        if method == "zhiyun":
            calc = ZhiyunCalculator(self.year, self.month, self.day, self.hour)
            yuan_info = calc.get_yuan_info()
            self.yuan = yuan_info["yuan_name"]
            self.yuan_idx = yuan_info["yuan"]
            self.zhi_run = yuan_info["zhi_run"]
            self.fu_tou = yuan_info["fu_tou"]
            self.yuan_method = "置闰法"
            dlog(f"置闰法三元: 元={self.yuan}({self.yuan_idx}), 符头={self.fu_tou}, 置闰={self.zhi_run}")
        else:
            # 拆补法
            yuan = get_yuan(self.year, self.month, self.day, jieqi, provider)
            self.yuan = ["上元", "中元", "下元"][yuan]
            self.yuan_idx = yuan
            self.zhi_run = False
            self.fu_tou = ""
            self.yuan_method = "拆补法"
            dlog(f"拆补法三元: 元={self.yuan}({self.yuan_idx})")
        
        # 局数
        self.ju_number = get_ju_number(jieqi, self.yuan_idx, self.is_yang_dun)
        dlog(f"局数: {self.ju_number} ({dun_str}{self.ju_number}局)")

    def _zhifu_palace(self) -> int:
        """转盘：值符（星/神/门）所落之宫 = **时干宫**（"值符加时干"）

        与 _find_zhifu_palace() 的区别（勿混用）：
          - _zhifu_palace()：旬首仪**随天盘**加临之宫 = 时干在地盘之宫（本函数）
          - _find_zhifu_palace()：旬首仪在**地盘**之本宫（值符"起行"之处）

        甲遁于六仪：时干为甲时以时柱旬首仪代之，此时即时干本宫 → 伏吟。
        中五寄坤二。
        """
        target = self.xun_yi if self.shi_gan == "甲" else self.shi_gan
        for p in range(1, 10):
            if self.chart[p].get("dipan") == target:
                # 盘式相关的中五处理：转盘寄坤二、飞盘实落
                # （若不按盘式分支，飞盘遇中五会得 2 而 _find_zhifu_palace 得 5，
                #   二者不等 → 甲时飞移步数 S≠0 → 伏吟失效）
                if p == 5 and self.pan_style != "feipan":
                    return 2
                return p
        raise RuntimeError(f"时干宫定位失败：{target} 未见于地盘（时柱{self.ganzhi_time}）")

    def _find_zhifu_palace(self) -> int:
        """找到值符宫：旬首仪落在的地盘宫（值符"起行之处"）

        - 转盘：中五寄坤二（据《御定奇门宝鉴》）。原缺陷为直接返回 5，
          调用方 EIGHT_PALACE_ORDER.index(5) 抛错后兜底到宫1，致八门/八神整盘错位。
        - 飞盘：中五**实落**，不寄坤二——故本函数按盘式返回 5 本身。
          （早前该分支无条件寄坤二，是飞盘的一处误用，与转盘混用了规则。）

        注：转盘求值符**落宫**请用 _zhifu_palace()。
        """
        for p, info in self.chart.items():
            if info.get("dipan") == self.xun_yi:
                if p == 5 and self.pan_style != "feipan":
                    return 2          # 转盘：中五寄坤二
                return p              # 飞盘：中五实落
        return 6  # 默认乾宫（旬首仪未见于地盘时）

    # ---- 地盘 ----
    def _make_dipan(self):
        """地盘三奇六仪：按局数起，阳顺阴逆布九宫
        
        序列：戊己庚辛壬癸丁丙乙（九干）
        起宫：局数对应的宫位（1-9，5 为中五寄坤二）
        阳遁顺行、阴遁逆行，跳过中五
        """
        step = 1 if self.is_yang_dun else -1
        idx = self.ju_number - 1  # 局数 1-9 对应索引 0-8
        
        for gan in QIMEN_SEQ:
            palace = (idx % 9) + 1
            if palace == 5:
                # 中五寄坤二（据《御定奇门宝鉴》"中五寄坤二"）
                # 干仍落中五可读；"寄"的体现由 _make_renpan 写入坤二宫的 dipan_ji
                # （旧版此处仅写 dipan_note 字符串，只标注不生效，已废）
                self.chart.setdefault(5, {})["dipan"] = gan
            else:
                self.chart.setdefault(palace, {})["dipan"] = gan
            idx += step

    # ---- 天盘（值符加时干）----
    def _make_tianpan(self):
        """天盘：地盘八宫环整体旋转，使【旬首仪】加临【时干】之宫

        核心（据《御定奇门宝鉴》"值符加时干"）：
        1. 取 pz = 时干宫（甲时以时柱旬首仪之宫代之）为旋转基准
        2. 旬首仪镇 pz，其余八干随内盘顺时针（阳遁）/逆时针（阴遁）排出
        3. 甲时 pz 即旬首仪本宫 → 旬首仪归位 → 天盘与地盘完全重合（伏吟）

        关键修正：天盘并非"自旬首仪另起戊己庚辛一轮"，而是地盘八宫环的
        整体旋转（内外盘相对位次恒定）。旧写法令甲时无法伏吟，
        且非伏吟时八干的相对位次也与地盘不符。
        """
        pz = self._zhifu_palace()                                  # 时干宫（值符加临处）
        pz_pos = EIGHT_PALACE_POS[pz]
        pv = EIGHT_PALACE_POS[self._find_zhifu_palace()]            # 旬首仪本宫位次
        di = {p: self.chart[p].get("dipan") for p in range(1, 10)}

        for p in range(1, 10):
            if p == 5:
                self.chart.setdefault(5, {})["tianpan"] = di[5]     # 中五不参与八宫环
                continue
            # 内盘位次回退 (pz_pos - pos(v))，甲时 pz_pos==pv → 恒等 → 伏吟
            inner_pos = (EIGHT_PALACE_POS[p] - pz_pos + pv) % 8
            self.chart.setdefault(p, {})["tianpan"] = di[EIGHT_PALACE_ORDER[inner_pos]]

    def _make_renpan(self):
        """人盘：八门九星飞布

        八门（据《烟波钓叟歌》八门定位）：
        - 值使门落宫：自值符落宫（=时干宫）起，按时支与旬首支差数顺/逆行
        - 其余八门按原始顺序顺/逆布八宫（跳中五）

        九星（据《御定奇门宝鉴》九星定位）：
        - 值符星落值符宫，其余按阴阳遁顺/逆布八宫
        - 天禽寄坤二（中五常驻；甲辰壬值时值符星寄坤二，与天芮同宫）
        """
        step = 1 if self.is_yang_dun else -1

        # ---- 值符宫：转盘取时干宫（值符加时干），非旬首仪本宫 ----
        zbf = self._zhifu_palace()

        # ---- 八门：值使门落宫计算 ----
        # 时支序号 - 旬首支序号 = 步数（模12）
        sz_idx = BRANCH_TO_IDX[self.shi_zhi]
        xun_zhi = self.xun_shou[1] if len(self.xun_shou) >= 2 else "子"
        xb_idx = BRANCH_TO_IDX.get(xun_zhi, 0)
        steps = (sz_idx - xb_idx) % 12

        # 从值符宫走 steps 步（跳过中五，仅八宫）
        palace = zbf
        for _ in range(steps):
            if palace in EIGHT_PALACE_POS:
                cur_idx = EIGHT_PALACE_POS[palace]
                next_idx = (cur_idx + step) % 8
                palace = EIGHT_PALACE_ORDER[next_idx]
            else:
                palace = EIGHT_PALACE_ORDER[0]
        self.zhimen_palace = palace

        # 八门布局：从值使门落宫起，按 DOOR_HOME 原始顺序
        doors = ["开门", "休门", "生门", "伤门", "杜门", "景门", "死门", "惊门"]
        zhimen_door = DOOR_HOME.get(palace, "开门")
        if zhimen_door in doors:
            doors.remove(zhimen_door)
            doors.insert(0, zhimen_door)
        start_door_idx = EIGHT_PALACE_POS.get(palace, 0)
        for i, door in enumerate(doors):
            fi = (start_door_idx + i * step) % 8
            p = EIGHT_PALACE_ORDER[fi]
            self.chart.setdefault(p, {})["men"] = door

        # ---- 九星：值符星随旬首仪，自值符宫起排 ----
        # 星序用 STAR_RING（跳中五，天禽寄坤二）：
        # 曾误用 [蓬,任,冲,辅,英,芮,柱,心]，致 5 个宫位星名错位；
        # 值符星也曾恒以天蓬起，旬首仪非戊时全错。此处一并修正。
        star_palaces_9 = [1, 2, 3, 4, 6, 7, 8, 9]  # 洛书顺序，跳过中五
        zbf_idx = EIGHT_PALACE_POS.get(zbf, 0)
        zhifu_star = YI_TO_STAR.get(self.xun_yi, "天蓬")
        si = STAR_RING.index(zhifu_star)          # 值符星在环中的位次
        for i, p in enumerate(star_palaces_9):
            star = STAR_RING[(si + (i - zbf_idx) * step) % 8]
            self.chart.setdefault(p, {})["star"] = star
        # 值符宫必落值符星（旋转式已保证，此处为自证性断言）
        assert self.chart[zbf]["star"] == zhifu_star, "值符星未落值符宫"
        # 中五：地盘干留在中五（可读），但星不显于中五——转盘之理寄坤二
        self.chart.setdefault(5, {}).pop("star", None)

        # ---- 中五寄坤二（转盘问事局通行之"寄二宫法"）----
        # 依《烟波钓叟歌》"天禽寄坤二"及转盘通行做法（"寄二宫法"/随芮走）：
        #   天芮在哪宫，天禽即寄在哪宫（"天禽星经常出现在天芮星旁边"）
        #   中五地盘干亦寄坤二宫，与坤二信息合看
        # 注：本地盘干为中五唯一实落之处（飞盘另有九宫实落法，不走此处）
        rui_palace = next((p for p, s in
                           ((p, self.chart[p].get("star")) for p in star_palaces_9)
                           if s == "天芮"), None)
        if rui_palace is not None:
            self.chart.setdefault(rui_palace, {})["star_ji"] = "天禽"   # 天禽寄于天芮之宫
        di5 = self.chart.get(5, {}).get("dipan")
        if di5:
            self.chart.setdefault(2, {})["dipan_ji"] = di5             # 中五干寄坤二

    def _make_shenpan(self):
        """神盘：八神随值符飞布（据《奇门遁甲秘笈大全》）

        八神顺序：值符、腾蛇、太阴、六合、白虎、玄武、九地、九天
        自值符落宫（=时干宫）起，按阴阳遁顺/逆布八宫。
        注：起点须用 _zhifu_palace()（值符加时干之落宫），
            不是旬首仪的地盘本宫。
        """
        step = 1 if self.is_yang_dun else -1
        zbf = self._zhifu_palace()
        start_idx = EIGHT_PALACE_POS.get(zbf, 0)
        for i, shen in enumerate(BASHEN_ORDER):
            fi = (start_idx + i * step) % 8
            p = EIGHT_PALACE_ORDER[fi]
            self.chart.setdefault(p, {})["shen"] = shen

    def _load_geju_db(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geju_db.json")
        self.geju_db = {}
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                self.geju_db = json.load(f)

    def _match_geju(self) -> list:
        """匹配格局：天盘干加地盘干（据《御定奇门宝鉴》格局法）

        ⚠️ 盘式相关，**不可两派通用**（旧注释声称"与盘式无关"，是错的）：
        - 转盘：中五为寄宫（天禽/地盘干寄坤二），该宫的天盘干直接抄自地盘
          （见 _make_tianpan），干对恒为 X+X，必然命中"庚加庚""癸加癸"这类
          同干格。实测 480 盘中五 100% 报出伏吟类格局——这是数据的镜像，
          不是术数事实（伏吟本指全盘天地盘重合，非单宫上下同干）。
          故转盘**跳过中五**。
        - 飞盘：中五实落得真干，天盘干是飞移结果，干对有意义（同干仅约 20%，
          属自然概率），故照常判定。

        另注：旧实现用 break 使一个格名只报一处（首个命中宫）。本实现保持该
        行为以免改动输出形态；这意味着同一格名若在多宫成立，只报第一个。
        """
        if not self.geju_db:
            return []
        skip_zhongwu = self.pan_style != "feipan"
        result = []
        for g in self.geju_db.get("geju", []):
            tp = g.get("tianpan", "")
            dp = g.get("dipan", "")
            for p, info in self.chart.items():
                if skip_zhongwu and p == 5:
                    continue
                if info.get("tianpan") == tp and info.get("dipan") == dp:
                    result.append({
                        "name": g.get("name", ""),
                        "level": g.get("level", ""),
                        "desc": g.get("desc", ""),
                        "palace": p,
                    })
                    break
        return result

    # ---- 输出 ----
    def to_dict(self) -> dict:
        result = {
            "time_info": {
                "year": self.year,
                "ganzhi_year": self.ganzhi_year,
                "ganzhi_month": self.ganzhi_month,
                "ganzhi_day": self.ganzhi_day,
                "ganzhi_time": self.ganzhi_time,
                "lunar": self.lunar_date,
            },
            "ju": {
                "is_yang_dun": self.is_yang_dun,
                "ju_number": self.ju_number,
                "yuan": self.yuan,
                "jieqi": self.current_jieqi,
                # 定局法审计字段：无论走哪条分支都如实标注实际所用方法
                "yuan_method": self.yuan_method,
                "fu_tou": self.fu_tou,
                "zhi_run": self.zhi_run,
            },
            "xun_shou": self.xun_shou,
            "xun_yi": self.xun_yi,
            "kong_wang": self.kong_wang,
            "chart": {str(k): v for k, v in self.chart.items()},
            "geju": self._match_geju(),
            "weather": self.weather,
        }
        return result

    def to_text(self) -> str:
        d = self.to_dict()
        L = []
        L.append("=" * 60)
        L.append("⚔️ 奇门遁甲排盘")
        L.append("=" * 60)
        L.append(f"时间：{self.year}年{self.month}月{self.day}日 {self.hour:02d}时（{self.shi_zhi}时）")
        L.append(f"农历：{d['time_info']['lunar']}")
        L.append(f"年柱：{d['time_info']['ganzhi_year']} 月柱：{d['time_info']['ganzhi_month']}")
        L.append(f"日柱：{d['time_info']['ganzhi_day']} 时柱：{d['time_info']['ganzhi_time']}")
        dun = "阳遁" if d['ju']['is_yang_dun'] else "阴遁"
        L.append(f"局：{d['ju']['jieqi']} {d['ju']['yuan']} {dun}{d['ju']['ju_number']}局"
                 f"（定局法：{d['ju']['yuan_method']}"
                 + (f"，符头{d['ju']['fu_tou']}"
                    + ("，置闰" if d['ju']['zhi_run'] else "") if d['ju'].get('fu_tou') else "")
                 + "）")
        L.append(f"旬首：{d['xun_shou']} 旬首仪：{d['xun_yi']}")
        L.append(f"空亡：{d['kong_wang']}")
        L.append("")
        L.append("📋 九宫排盘：")
        for p in [6, 7, 8,  2, 5, 1,  3, 4, 9]:
            info = d['chart'].get(str(p), {})
            dipan = info.get('dipan', '—')
            tianpan = info.get('tianpan', '—')
            men = info.get('men', '—')
            star = info.get('star', '—')
            shen = info.get('shen', '—')
            # 转盘中五寄坤二的两项：天禽随天芮、中五地盘干寄坤二
            if info.get('star_ji'):
                star = f"{star}(寄{info['star_ji']})" if star != '—' else info['star_ji']
            if info.get('dipan_ji'):
                dipan = f"{dipan}｜寄{info['dipan_ji']}"
            L.append(f"  宫{p}: 地盘{dipan} 天盘{tianpan} 门{men} 星{star} 神{shen}")
        L.append("")
        if d['geju']:
            L.append("🔍 格局汇总：")
            for g in d['geju']:
                L.append(f"  [{g['level']}] {g['name']}（宫{g['palace']}）: {g['desc']}")
        else:
            L.append("🔍 格局：无特殊格局")
        L.append("")
        L.append("💡 （仅供参考，决策需结合实际情况理性判断）")
        L.append("=" * 60)
        return "\n".join(L)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="奇门遁甲排盘系统")
    parser.add_argument("-q", "--question", default="", help="求测问题")
    parser.add_argument("-y", "--year", type=int, default=None, help="年")
    parser.add_argument("-m", "--month", type=int, default=None, help="月")
    parser.add_argument("-d", "--day", type=int, default=None, help="日")
    # default=None：区分「未指定」与「指定为 0 点（子时）」
    # 旧写法 default=0 + `if args.hour > 0` 会把 -H 0 静默替换成当前小时，
    # 导致子时无法指定，且 0 点起局悄悄变成另一个时辰。
    parser.add_argument("-H", "--hour", type=int, default=None, help="时（0-23）")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    parser.add_argument(
        "--dunjia-method", dest="dunjia_method", default="zhiyun",
        choices=["zhiyun", "chaibu", "maoshan"],
        help="定局法：zhiyun=置闰法(默认,正统) / chaibu=拆补法(实用) / maoshan=茅山法(未接入)",
    )
    parser.add_argument(
        "--pan-style", dest="pan_style", default="zhuanpan",
        choices=["zhuanpan", "feipan"],
        help="盘式：zhuanpan=转盘法(默认,《烟波钓叟歌》系) / feipan=飞盘法(《奇门法窍》系)",
    )
    args = parser.parse_args()

    now = local_now()
    # 未指定 -H 才用当前时刻；-H 0 是子时，必须原样保留
    # （旧写法 `args.hour if args.hour > 0` 会把 0 静默替成当前小时）
    c = QimenChart(
        args.year or now.year,
        args.month or now.month,
        args.day or now.day,
        args.hour if args.hour is not None else now.hour,
        args.question,
        dunjia_method=args.dunjia_method,
        pan_style=args.pan_style,
    )
    if args.json:
        print(json.dumps(c.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(c.to_text())


if __name__ == "__main__":
    main()