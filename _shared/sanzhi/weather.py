"""
天气分析模块（统一接口）
奇门遁甲、大六壬、太乙神数可共用的天气分析接口
实际算法由各派系自行实现，此处提供统一数据结构和基类
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class WeatherSignal:
    """单一气象信号"""
    type: str          # 信号类型：雨、风、极端、不稳定等
    level: str         # 等级：轻、中、重、特大
    direction: str     # 方位：对应宫位/方向
    description: str   # 描述
    confidence: float  # 置信度 0-1


@dataclass
class WeatherAnalysis:
    """天气分析结果"""
    trend: str = "平稳"           # 总体趋势：平稳/多变/剧烈
    rain: List[WeatherSignal] = field(default_factory=list)      # 雨水信号
    wind: List[WeatherSignal] = field(default_factory=list)      # 风信号
    extreme: List[WeatherSignal] = field(default_factory=list)   # 极端天气
    instability: List[WeatherSignal] = field(default_factory=list)  # 不稳定因素
    confidence: float = 0.0       # 综合置信度
    
    # 原始数据（供高级分析使用）
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "trend": self.trend,
            "rain": [{"type": s.type, "level": s.level, "direction": s.direction,
                      "description": s.description, "confidence": s.confidence} 
                     for s in self.rain],
            "wind": [{"type": s.type, "level": s.level, "direction": s.direction,
                      "description": s.description, "confidence": s.confidence}
                     for s in self.wind],
            "extreme": [{"type": s.type, "level": s.level, "direction": s.direction,
                         "description": s.description, "confidence": s.confidence}
                        for s in self.extreme],
            "instability": [{"type": s.type, "level": s.level, "direction": s.direction,
                             "description": s.description, "confidence": s.confidence}
                            for s in self.instability],
            "confidence": self.confidence,
        }
    
    @classmethod
    def empty(cls) -> "WeatherAnalysis":
        """返回空分析结果（兼容无天气功能的场合）"""
        return cls(trend="无数据", confidence=0.0)


class WeatherAnalyzer(ABC):
    """天气分析器抽象基类"""
    
    @abstractmethod
    def analyze(self, chart_data: Dict[str, Any]) -> WeatherAnalysis:
        """
        根据排盘数据分析天气
        chart_data: 各派系排盘的核心数据字典
        """
        pass
    
    def to_dict(self) -> Dict:
        """默认实现：返回空分析"""
        return WeatherAnalysis.empty().to_dict()


class DefaultWeatherAnalyzer(WeatherAnalyzer):
    """默认天气分析器（占位，不崩溃）"""
    
    def analyze(self, chart_data: Dict[str, Any]) -> WeatherAnalysis:
        return WeatherAnalysis.empty()


# 全局默认分析器
_default_analyzer: Optional[WeatherAnalyzer] = None


def get_default_analyzer() -> WeatherAnalyzer:
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = DefaultWeatherAnalyzer()
    return _default_analyzer


def set_default_analyzer(analyzer: WeatherAnalyzer) -> None:
    global _default_analyzer
    _default_analyzer = analyzer


__all__ = [
    "WeatherSignal", "WeatherAnalysis", "WeatherAnalyzer",
    "DefaultWeatherAnalyzer", "get_default_analyzer", "set_default_analyzer",
]