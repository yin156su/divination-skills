"""
统一日志配置
三式术数统一的日志输出格式和级别控制
"""

import logging
import sys
from typing import Optional


# 默认日志格式
DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%H:%M:%S"


# 预定义 logger 名称
LOGGER_QIMEN = "sanzhi.qimen"
LOGGER_LIUREN = "sanzhi.liuren"
LOGGER_TAIYI = "sanzhi.taiyi"
LOGGER_CORE = "sanzhi.core"


# 模块级缓存
_loggers = {}
_configured = False


def setup_logging(level: int = logging.INFO,
                  format_str: str = DEFAULT_FORMAT,
                  date_format: str = DEFAULT_DATE_FORMAT,
                  stream=None) -> None:
    """
    配置全局日志（仅需调用一次）
    """
    global _configured
    if _configured:
        return
    
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(logging.Formatter(format_str, date_format))
    
    root_logger = logging.getLogger("sanzhi")
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    root_logger.propagate = False
    
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger
    自动挂载到 sanzhi 命名空间下
    """
    if not name.startswith("sanzhi."):
        name = f"sanzhi.{name}"
    
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
        # 如果根 logger 未配置，自动配置默认
        if not _configured:
            setup_logging()
    
    return _loggers[name]


def set_level(level: int, name: str = "sanzhi") -> None:
    """设置指定 logger 的级别"""
    logger = logging.getLogger(name)
    logger.setLevel(level)


# 便捷函数
def debug(msg: str, name: str = "core") -> None:
    get_logger(name).debug(msg)


def info(msg: str, name: str = "core") -> None:
    get_logger(name).info(msg)


def warning(msg: str, name: str = "core") -> None:
    get_logger(name).warning(msg)


def error(msg: str, name: str = "core") -> None:
    get_logger(name).error(msg)


__all__ = [
    "setup_logging",
    "get_logger",
    "set_level",
    "debug", "info", "warning", "error",
    "LOGGER_QIMEN", "LOGGER_LIUREN", "LOGGER_TAIYI", "LOGGER_CORE",
]