"""
农历提供者抽象模块
统一 lunar_python 等底层库的调用接口，便于未来替换或测试
"""

from typing import Optional, Protocol, Any
from dataclasses import dataclass
from datetime import date
from abc import ABC, abstractmethod


@dataclass
class LunarData:
    """农历数据统一容器"""
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    second: int = 0
    
    # 干支
    ganzhi_year: str = ""   # 年柱
    ganzhi_month: str = ""  # 月柱
    ganzhi_day: str = ""    # 日柱
    ganzhi_time: str = ""   # 时柱
    
    # 农历日期
    lunar_year: int = 0
    lunar_month: int = 0
    lunar_day: int = 0
    is_leap_month: bool = False
    lunar_month_name: str = ""
    lunar_day_name: str = ""
    
    # 节气
    prev_jieqi_name: str = ""
    prev_jieqi_type: str = ""  # "节" or "中"
    prev_jieqi_date: Optional[date] = None
    next_jieqi_name: str = ""
    next_jieqi_type: str = ""
    next_jieqi_date: Optional[date] = None
    jieqi_table: dict = None  # 完整节气表 {name: date}
    
    def __post_init__(self):
        if self.jieqi_table is None:
            self.jieqi_table = {}


class LunarProvider(ABC):
    """农历提供者抽象基类"""
    
    @abstractmethod
    def get_lunar_data(self, year: int, month: int, day: int, 
                       hour: int = 0, minute: int = 0, second: int = 0) -> LunarData:
        """获取完整农历数据"""
        pass
    
    @abstractmethod
    def get_solar(self, year: int, month: int, day: int, 
                  hour: int = 0, minute: int = 0, second: int = 0) -> Any:
        """获取底层 Solar 对象（供高级用法）"""
        pass


class DefaultLunarProvider(LunarProvider):
    """基于 lunar_python 的默认实现"""
    
    def __init__(self):
        self._solar_class = None
        self._init_lunar_python()
    
    def _init_lunar_python(self):
        try:
            from lunar_python import Solar
            self._solar_class = Solar
        except ImportError:
            raise ImportError("需要安装 lunar-python: pip install lunar-python")
    
    def get_solar(self, year: int, month: int, day: int, 
                  hour: int = 0, minute: int = 0, second: int = 0):
        if self._solar_class is None:
            self._init_lunar_python()
        return self._solar_class(year, month, day, hour, minute, second)
    
    def get_lunar_data(self, year: int, month: int, day: int,
                       hour: int = 0, minute: int = 0, second: int = 0) -> LunarData:
        s = self.get_solar(year, month, day, hour, minute, second)
        l = s.getLunar()
        
        data = LunarData(
            year=year, month=month, day=day, hour=hour, minute=minute, second=second,
            ganzhi_year=l.getYearInGanZhi(),
            ganzhi_month=l.getMonthInGanZhi(),
            ganzhi_day=l.getDayInGanZhi(),
            ganzhi_time=l.getTimeInGanZhi(),
            lunar_year=l.getYear(),
            lunar_month=l.getMonth(),
            lunar_day=l.getDay(),
            is_leap_month=False,  # lunar_python doesn't expose leap month directly
            lunar_month_name=l.getMonthInChinese(),
            lunar_day_name=l.getDayInChinese(),
        )
        
        # 前一节气
        prev_jq = l.getPrevJieQi()
        if prev_jq and hasattr(prev_jq, "getName"):
            data.prev_jieqi_name = prev_jq.getName()
            data.prev_jieqi_type = "中" if "至" in data.prev_jieqi_name or "分" in data.prev_jieqi_name else "节"
            if hasattr(prev_jq, "getYear"):
                data.prev_jieqi_date = date(prev_jq.getYear(), prev_jq.getMonth(), prev_jq.getDay())
        
        # 后一节气
        next_jq = l.getNextJieQi()
        if next_jq and hasattr(next_jq, "getName"):
            data.next_jieqi_name = next_jq.getName()
            data.next_jieqi_type = "中" if "至" in data.next_jieqi_name or "分" in data.next_jieqi_name else "节"
            if hasattr(next_jq, "getYear"):
                data.next_jieqi_date = date(next_jq.getYear(), next_jq.getMonth(), next_jq.getDay())
        
        # 完整节气表
        table = l.getJieQiTable()
        if table:
            for name, jq in table.items():
                if hasattr(jq, "getYear"):
                    data.jieqi_table[name] = date(jq.getYear(), jq.getMonth(), jq.getDay())
        
        return data


# 全局默认实例
_default_provider: Optional[DefaultLunarProvider] = None


def get_default_provider() -> DefaultLunarProvider:
    """获取全局默认农历提供者（单例）"""
    global _default_provider
    if _default_provider is None:
        _default_provider = DefaultLunarProvider()
    return _default_provider


def set_default_provider(provider: LunarProvider) -> None:
    """设置全局默认农历提供者（用于测试或替换实现）"""
    global _default_provider
    _default_provider = provider


__all__ = [
    "LunarData", "LunarProvider", "DefaultLunarProvider",
    "get_default_provider", "set_default_provider",
]