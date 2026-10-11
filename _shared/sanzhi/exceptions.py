"""
统一异常体系
三式术数专用异常类型
"""

class SanZhiError(Exception):
    """三式术数基础异常"""
    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(f"{message}: {detail}" if detail else message)


class LunarCalcError(SanZhiError):
    """农历计算异常（如 lunar_python 调用失败、节气获取失败）"""
    pass


class InvalidDateTimeError(SanZhiError):
    """非法日期时间异常"""
    pass


class ChartGenerationError(SanZhiError):
    """排盘生成异常（如天盘构建失败、格局匹配失败）"""
    pass


class InvalidParameterError(SanZhiError):
    """参数错误（如干支不匹配、五行不存在）"""
    pass


class ConfigurationError(SanZhiError):
    """配置错误（如格局库缺失、常量表错误）"""
    pass


class ProviderError(SanZhiError):
    """农历提供者异常"""
    pass


__all__ = [
    "SanZhiError",
    "LunarCalcError",
    "InvalidDateTimeError",
    "ChartGenerationError",
    "InvalidParameterError",
    "ConfigurationError",
    "ProviderError",
]