"""
三式术数共享核心库 (SanZhi Shared Core)
统一奇门遁甲、大六壬、太乙神数的基础设施

核心模块：
- ganzhi: 干支系统（六十甲子、旬首、旬空、时辰、寄宫）
- wuxing: 五行系统（生克制化、纳音、旺衰）
- dizhi: 地支系统（六冲六合三合三会、刑害、藏干）
- jieqi: 节气系统（二十四节气、中气、月将、阴阳遁）
- lunar: 农历提供者抽象（支持 lunar_python、未来可插拔）
- datetime: 统一时间处理
- exceptions: 统一异常体系
- logging: 统一日志配置
"""

from .ganzhi import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
    STEM_TO_IDX, BRANCH_TO_IDX,
    LIUSHI_JIAZI,
    YANG_STEMS, YIN_STEMS, YANG_BRANCHES, YIN_BRANCHES,
    XUN_SHOU_YI, XUN_KONG, STEM_ELEMENT, BRANCH_ELEMENT,
    get_shichen, get_xun_shou, get_kong_wang,
    get_ganzhi_from_stem_branch, get_liushijiazi,
    GAN_GONG,  # 日干寄宫
    LunarGanZhi,
)
from .wuxing import (
    ELEMENT_MAP, SHENG_KE,
    WOOD, FIRE, EARTH, METAL, WATER,
    FIVE_ELEMENTS,
    RELATION_SHENG, RELATION_KE, RELATION_XIE,
    RELATION_BEI_KE, RELATION_BI_HE, RELATION_WU_GUAN,
    get_relation, get_wangxiang, get_nayin, NAYIN_MAP,
    get_stem_element, get_branch_element, get_ganzhi_element,
)
from .dizhi import (
    is_liu_chong, is_liu_he, get_he, get_sanhe, get_san_hui,
    get_xing, get_hai, get_zhi_wuxing, get_zhi_yinyang,
    get_zhi_canggan, get_zhi_zhengqi, get_zhi_zhongqi, get_zhi_yuqi,
    YIMA_MAP, WENCHANG_MAP, HUAGAI_MAP, JIESHA_MAP, ZAISHA_MAP,
    LIU_CHONG, LIU_HE, SAN_HE, SAN_HUI, XING, HAI,
    ZHI_CANGGAN, ZHI_ZHENGQI, ZHI_ZHONGQI, ZHI_YUQI,
    get_chong_sha, get_relations_for_zhi,
)
from .jieqi import (
    JIEQI_LIST, JIEQI_TYPE, ZHONGQI_YUEJIANG, ZHONGQI_MAP, YUEJIANG_MAP, JIEQI_ORDER,
    get_current_jieqi, get_yuejiang, get_yang_yin_dun,
    is_yang_dun, get_yuan,
    YANG_DUN_JIEQI, YIN_DUN_JIEQI,
    YANG_JU_TABLE, YIN_JU_TABLE, get_ju_number,
    JieQiInfo,
)
from .lunar import LunarProvider, DefaultLunarProvider, LunarData, get_default_provider, set_default_provider
from .datetime_utils import DateTimeArgs, parse_datetime_args, get_current_datetime, validate_datetime, format_datetime_chinese, local_now, LOCAL_TZ
from .exceptions import SanZhiError, LunarCalcError, InvalidDateTimeError, ChartGenerationError, InvalidParameterError, ConfigurationError, ProviderError
from .logging_config import get_logger, setup_logging, debug, info, warning, error, LOGGER_QIMEN, LOGGER_LIUREN, LOGGER_TAIYI, LOGGER_CORE
from .weather import WeatherSignal, WeatherAnalysis, WeatherAnalyzer, DefaultWeatherAnalyzer, get_default_analyzer, set_default_analyzer

__version__ = "1.0.0"

__all__ = [
    # ganzhi
    "HEAVENLY_STEMS", "EARTHLY_BRANCHES",
    "STEM_TO_IDX", "BRANCH_TO_IDX",
    "LIUSHI_JIAZI",
    "YANG_STEMS", "YIN_STEMS", "YANG_BRANCHES", "YIN_BRANCHES",
    "XUN_SHOU_YI", "XUN_KONG", "STEM_ELEMENT", "BRANCH_ELEMENT",
    "get_shichen", "get_xun_shou", "get_kong_wang",
    "get_ganzhi_from_stem_branch", "get_liushijiazi",
    "GAN_GONG",
    "LunarGanZhi",
    # wuxing
    "ELEMENT_MAP", "SHENG_KE",
    "WOOD", "FIRE", "EARTH", "METAL", "WATER",
    "FIVE_ELEMENTS",
    "RELATION_SHENG", "RELATION_KE", "RELATION_XIE",
    "RELATION_BEI_KE", "RELATION_BI_HE", "RELATION_WU_GUAN",
    "get_relation", "get_wangxiang", "get_nayin", "NAYIN_MAP",
    "get_stem_element", "get_branch_element", "get_ganzhi_element",
    # dizhi
    "is_liu_chong", "is_liu_he", "get_he", "get_sanhe", "get_san_hui",
    "get_xing", "get_hai", "get_zhi_wuxing", "get_zhi_yinyang",
    "get_zhi_canggan", "get_zhi_zhengqi", "get_zhi_zhongqi", "get_zhi_yuqi",
    "YIMA_MAP", "WENCHANG_MAP", "HUAGAI_MAP", "JIESHA_MAP", "ZAISHA_MAP",
    "LIU_CHONG", "LIU_HE", "SAN_HE", "SAN_HUI", "XING", "HAI",
    "ZHI_CANGGAN", "ZHI_ZHENGQI", "ZHI_ZHONGQI", "ZHI_YUQI",
    "get_chong_sha", "get_relations_for_zhi",
    # jieqi
    "JIEQI_LIST", "ZHONGQI_MAP", "YUEJIANG_MAP",
    "get_current_jieqi", "get_yuejiang", "get_yang_yin_dun",
    "is_yang_dun", "get_yuan",
    "YANG_DUN_JIEQI", "YIN_DUN_JIEQI",
    "YANG_JU_TABLE", "YIN_JU_TABLE", "get_ju_number",
    "JieQiInfo",
    # lunar
    "LunarProvider", "DefaultLunarProvider", "LunarData",
    "get_default_provider", "set_default_provider",
    # datetime
    "DateTimeArgs", "parse_datetime_args", "get_current_datetime",
    "validate_datetime", "format_datetime_chinese", "local_now", "LOCAL_TZ",
    # exceptions
    "SanZhiError", "LunarCalcError", "InvalidDateTimeError", "ChartGenerationError",
    "InvalidParameterError", "ConfigurationError", "ProviderError",
    # logging
    "get_logger", "setup_logging", "debug", "info", "warning", "error",
    "LOGGER_QIMEN", "LOGGER_LIUREN", "LOGGER_TAIYI", "LOGGER_CORE",
    # weather
    "WeatherSignal", "WeatherAnalysis", "WeatherAnalyzer",
    "DefaultWeatherAnalyzer", "get_default_analyzer", "set_default_analyzer",
]