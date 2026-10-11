"""
统一时间处理模块
处理命令行参数解析、当前时间获取、时间验证等通用逻辑
"""

from typing import Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import argparse
import os

# ============================================================
# 本地时区
# ------------------------------------------------------------
# 运行环境（Ubuntu/proot 沙箱）的 /etc/localtime 常指向 Etc/UTC 且 TZ 为空，
# 此时 datetime.now() 返回的是 UTC 时刻。但术数起局必须用求测者所在地的
# 地方时：若按 UTC 取时，盘面会整体偏 8 小时，时辰、时柱乃至日柱全错。
# 故缺省按东八区；若外部显式设置了 TZ 则尊重之；zoneinfo 不可用时退化为固定 +8。
# ============================================================
LOCAL_TZ = timezone(timedelta(hours=8))


def local_now() -> datetime:
    """获取本地当前时间（缺省东八区，TZ 已设置时按其解释）。"""
    tz_name = os.environ.get("TZ")
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
    return datetime.now(LOCAL_TZ)


@dataclass
class DateTimeArgs:
    """统一的时间参数容器"""
    year: int
    month: int
    day: int
    hour: int
    question: str = ""
    calc_type: str = "year"  # 用于太乙：year/month/day/hour
    
    @property
    def has_custom_time(self) -> bool:
        """是否指定了自定义时间（非全部默认）"""
        return self.year != 0 or self.month != 0 or self.day != 0 or self.hour != 0


def parse_datetime_args(args: Optional[argparse.Namespace] = None,
                         parser: Optional[argparse.ArgumentParser] = None) -> DateTimeArgs:
    """
    解析命令行时间参数（三式通用）
    支持：-y 年 -m 月 -d 日 -H 时 -q 问题 -t 类型(太乙专用)
    """
    if args is None:
        # 如果没有传入已解析的 args，创建默认解析器
        if parser is None:
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument("-q", "--question", default="", help="求测问题")
            parser.add_argument("-y", "--year", type=int, default=0, help="年")
            parser.add_argument("-m", "--month", type=int, default=0, help="月")
            parser.add_argument("-d", "--day", type=int, default=0, help="日")
            parser.add_argument("-H", "--hour", type=int, default=None, help="时(0-23)")
            parser.add_argument("-t", "--type", default="year", 
                              choices=["year", "month", "day", "hour"], 
                              help="计算类型(太乙专用)")
        args = parser.parse_args()
    
    now = local_now()
    
    return DateTimeArgs(
        year=args.year or now.year,
        month=args.month or now.month,
        day=args.day or now.day,
        # 未指定才取当前小时；-H 0 是合法的子时
        hour=args.hour if args.hour is not None else now.hour,
        question=args.question if hasattr(args, 'question') else "",
        calc_type=getattr(args, 'type', 'year'),
    )
def get_current_datetime() -> Tuple[int, int, int, int]:
    """获取当前年月日时"""
    now = local_now()
    return now.year, now.month, now.day, now.hour


def validate_datetime(year: int, month: int, day: int, hour: int) -> bool:
    """验证日期时间合法性"""
    try:
        datetime(year, month, day, hour)
        return True
    except ValueError:
        return False


def format_datetime_chinese(year: int, month: int, day: int, hour: int) -> str:
    """格式化为中文时间字符串"""
    return f"{year}年{month}月{day}日 {hour}时"


__all__ = [
    "DateTimeArgs",
    "parse_datetime_args",
    "get_current_datetime",
    "validate_datetime",
    "format_datetime_chinese",
]