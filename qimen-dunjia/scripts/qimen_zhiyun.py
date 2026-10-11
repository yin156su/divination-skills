#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲·置闰法定局（正统实现）
据源：《烟波钓叟歌》《御定奇门宝鉴》《协纪辨方书》

核心算法（正统置闰法）：
1. 从冬至（阳遁起点）或夏至（阴遁起点）开始计算符头序列
2. 符头为甲己日，每符头管5天
3. 12符头循环：上元(甲子/甲午/己卯/己酉) → 中元(甲寅/甲申/己巳/己亥) → 下元(甲辰/甲戌/己丑/己未)
4. 超神（符头先到节气）>9天时，在芒种/大雪后置闰
"""

import os, sys
# 定位共享历法库 sanzhi：兼容部署布局(shared_assets/sanzhi)与仓库布局(_shared)
_d = os.path.dirname(os.path.abspath(__file__))
while (not os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
       and not os.path.isdir(os.path.join(_d, "_shared"))
       and os.path.dirname(_d) != _d):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "shared_assets", "sanzhi") if os.path.isdir(os.path.join(_d, "shared_assets", "sanzhi"))
                else os.path.join(_d, "_shared"))

from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from sanzhi import (
    DefaultLunarProvider,
    JIEQI_LIST, JIEQI_TYPE,
    YANG_DUN_JIEQI, YIN_DUN_JIEQI,
    YANG_JU_TABLE, YIN_JU_TABLE,
    is_yang_dun, get_ju_number,
)


# ============================================================
# 符头定义
# ============================================================

# 12符头标准顺序（按《烟波钓叟歌》）
FU_TOU_SEQUENCE = [
    "甲子", "甲午", "己卯", "己酉",   # 上元
    "甲寅", "甲申", "己巳", "己亥",   # 中元
    "甲辰", "甲戌", "己丑", "己未",   # 下元
]

# 符头→三元映射
FU_TOU_TO_YUAN = {
    "甲子": "上元", "甲午": "上元", "己卯": "上元", "己酉": "上元",
    "甲寅": "中元", "甲申": "中元", "己巳": "中元", "己亥": "中元",
    "甲辰": "下元", "甲戌": "下元", "己丑": "下元", "己未": "下元",
}


@dataclass
class FuTouInfo:
    """符头信息"""
    fu_tou: str          # 符头干支
    yuan: str            # 上元/中元/下元
    start_date: date     # 符头起始日期
    jieqi: str           # 所属节气
    is_zhi_run: bool     # 是否置闰
    chao_shen_days: int  # 超神天数


class ZhiyunCalculator:
    """置闰法计算器（正统实现）
    
    正统置闰法规则（据《烟波钓叟歌》）：
    1. 以冬至/夏至为周期起点
    2. 符头甲己日定三元，每符头5天
    3. 超神>9天时在芒种/大雪后置闰
    """
    
    def __init__(self, year: int, month: int, day: int, hour: int = 12):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.target_date = date(year, month, day)
        
        self.provider = DefaultLunarProvider()
        self.jieqi_dates = self._get_jieqi_dates()
        self.fu_tou_list = self._calculate_fu_tou()
        self.current_fu_tou = self._find_current()
        
    def _get_jieqi_dates(self) -> Dict[str, date]:
        """获取节气日期"""
        result = {}
        for name in JIEQI_LIST:
            d = self._get_jieqi_date(self.year, name)
            if d:
                result[name] = d
        # 含上年冬至
        dz = self._get_jieqi_date(self.year - 1, "冬至")
        if dz:
            result["冬至_上年"] = dz
        return result
    
    def _get_jieqi_date(self, year: int, name: str) -> Optional[date]:
        """获取节气日期"""
        try:
            from lunar_python import Solar
            # 近似日期
            approx = {
                "冬至": (12, 21), "小寒": (1, 5), "大寒": (1, 20),
                "立春": (2, 4), "雨水": (2, 19), "惊蛰": (3, 5),
                "春分": (3, 20), "清明": (4, 5), "谷雨": (4, 20),
                "立夏": (5, 5), "小满": (5, 21), "芒种": (6, 5),
                "夏至": (6, 21), "小暑": (7, 7), "大暑": (7, 22),
                "立秋": (8, 7), "处暑": (8, 23), "白露": (9, 7),
                "秋分": (9, 23), "寒露": (10, 8), "霜降": (10, 23),
                "立冬": (11, 7), "小雪": (11, 22), "大雪": (12, 7),
            }
            m, d = approx.get(name, (1, 1))
            s = Solar(year, m, d, 12, 0, 0)
            l = s.getLunar()
            jq = l.getJieQiTable().get(name)
            if jq:
                return date(jq.getYear(), jq.getMonth(), jq.getDay())
        except:
            pass
        return None
    
    def _get_ganzhi(self, d: date) -> str:
        """获取日干支"""
        try:
            from lunar_python import Solar
            return Solar(d.year, d.month, d.day, 12, 0, 0).getLunar().getDayInGanZhi()
        except:
            return "甲子"
    
    def _find_first_fu_tou(self, start: date) -> date:
        """找到start后第一个符头（甲己日）"""
        for i in range(60):
            d = start + timedelta(days=i)
            if self._get_ganzhi(d)[0] in ("甲", "己"):
                return d
        return start
    
    def _calculate_fu_tou(self) -> List[FuTouInfo]:
        """计算符头序列（正统置闰法）
        
        关键：每个遁局周期（阳遁从冬至，阴遁从夏至）独立计算符头序列
        """
        result = []
        
        # 找到目标日期所在的遁局起点
        dongzhi = self.jieqi_dates.get("冬至")
        xiazhi = self.jieqi_dates.get("夏至")
        prev_dongzhi = self.jieqi_dates.get("冬至_上年")
        
        # 确定基准点
        if self.target_date >= dongzhi and (not xiazhi or self.target_date < xiazhi):
            # 阳遁周期
            base = dongzhi
        elif prev_dongzhi and self.target_date >= prev_dongzhi:
            # 上一个冬至后
            base = prev_dongzhi
        else:
            # 阴遁周期
            base = xiazhi if xiazhi else prev_dongzhi
        
        # 找到基准点后第一个符头
        first_ft = self._find_first_fu_tou(base)
        
        # 生成符头序列（覆盖目标日期前后）
        for i in range(200):
            ft_date = first_ft + timedelta(days=i * 5)
            ft_ganzhi = self._get_ganzhi(ft_date)
            
            # 跳过非符头日（理论上不会发生，因为步长是5天）
            if ft_ganzhi[0] not in ("甲", "己"):
                continue
            
            # 找所属节气
            jieqi, jq_date = self._find_jieqi(ft_date)
            
            # 三元由符头干支决定
            yuan = FU_TOU_TO_YUAN.get(ft_ganzhi, "上元")
            
            # 超神天数
            chao_shen = (ft_date - jq_date).days if jieqi and jq_date else 0
            
            result.append(FuTouInfo(
                fu_tou=ft_ganzhi,
                yuan=yuan,
                start_date=ft_date,
                jieqi=jieqi or "",
                is_zhi_run=False,
                chao_shen_days=chao_shen,
            ))
        
        # 应用置闰规则
        result = self._apply_zhi_run(result)
        
        return result
    
    def _find_jieqi(self, d: date) -> Tuple[Optional[str], Optional[date]]:
        """找到d所属的节气（前一节气）"""
        sorted_jq = sorted([(k, v) for k, v in self.jieqi_dates.items() if not k.endswith("_上年")],
                          key=lambda x: x[1])
        prev = None
        for name, jq_date in sorted_jq:
            if jq_date <= d:
                prev = (name, jq_date)
            else:
                break
        return prev if prev else (None, None)
    
    def _apply_zhi_run(self, lst: List[FuTouInfo]) -> List[FuTouInfo]:
        """应用置闰规则"""
        result = list(lst)
        
        # 找每个节气的最后符头
        last_by_jq = {}
        for ft in reversed(result):
            if ft.jieqi and ft.jieqi not in last_by_jq:
                last_by_jq[ft.jieqi] = ft
        
        # 芒种置闰
        mg = last_by_jq.get("芒种")
        xz = self.jieqi_dates.get("夏至")
        if mg and xz and mg.chao_shen_days > 9:
            # 在夏至前插入置闰符头
            insert_pos = next((i for i, ft in enumerate(result) if ft.start_date >= xz), len(result))
            for yuan in ["上元", "中元", "下元"]:
                result.insert(insert_pos, FuTouInfo(
                    fu_tou=mg.fu_tou, yuan=yuan, start_date=xz,
                    jieqi="芒种", is_zhi_run=True, chao_shen_days=mg.chao_shen_days
                ))
                xz += timedelta(days=5)
        
        # 大雪置闰
        dx = last_by_jq.get("大雪")
        xh = self.jieqi_dates.get("小寒")
        if dx and xh and dx.chao_shen_days > 9:
            insert_pos = next((i for i, ft in enumerate(result) if ft.start_date >= xh), len(result))
            for yuan in ["上元", "中元", "下元"]:
                result.insert(insert_pos, FuTouInfo(
                    fu_tou=dx.fu_tou, yuan=yuan, start_date=xh,
                    jieqi="大雪", is_zhi_run=True, chao_shen_days=dx.chao_shen_days
                ))
                xh += timedelta(days=5)
        
        return result
    
    def _find_current(self) -> Optional[FuTouInfo]:
        """找目标日期所属符头"""
        for ft in self.fu_tou_list:
            if ft.start_date <= self.target_date < ft.start_date + timedelta(days=5):
                return ft
        return None
    
    def get_yuan_info(self) -> Dict:
        """获取三元信息"""
        if not self.current_fu_tou:
            return {"yuan": 0, "yuan_name": "上元", "fu_tou": "甲子", "zhi_run": False}
        
        return {
            "yuan": {"上元": 0, "中元": 1, "下元": 2}.get(self.current_fu_tou.yuan, 0),
            "yuan_name": self.current_fu_tou.yuan,
            "fu_tou": self.current_fu_tou.fu_tou,
            "zhi_run": self.current_fu_tou.is_zhi_run,
        }


def get_yuan_zhiyun(year, month, day, jieqi_name=None, lunar_provider=None):
    """兼容接口"""
    return ZhiyunCalculator(year, month, day).get_yuan_info()["yuan"]


if __name__ == "__main__":
    print("=== 置闰法测试 ===")
    tests = [
        (2026, 1, 15, "冬至后"),
        (2026, 6, 21, "夏至"),
        (2026, 8, 23, "处暑日"),
        (2026, 8, 31, "处暑后"),  # 关键
        (2026, 12, 7, "大雪"),
    ]
    for y, m, d, desc in tests:
        c = ZhiyunCalculator(y, m, d)
        info = c.get_yuan_info()
        print(f"{desc}: {info['yuan_name']}({info['yuan']}), 符头={info['fu_tou']}")