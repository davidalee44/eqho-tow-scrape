"""Time period calculation utilities"""
from datetime import datetime, timedelta
from typing import Tuple
from enum import Enum


class TimePeriod(str, Enum):
    """Time period options"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    LAST_7_DAYS = "last_7_days"
    LAST_14_DAYS = "last_14_days"
    LAST_30_DAYS = "last_30_days"


def get_time_period_range(period: str) -> Tuple[datetime, datetime]:
    """
    Get start and end datetime for a time period
    
    Returns:
        (start_datetime, end_datetime)
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if period == TimePeriod.TODAY:
        start = today_start
        end = now
    elif period == TimePeriod.YESTERDAY:
        start = today_start - timedelta(days=1)
        end = today_start
    elif period == TimePeriod.THIS_WEEK:
        # Monday of this week
        days_since_monday = now.weekday()
        start = today_start - timedelta(days=days_since_monday)
        end = now
    elif period == TimePeriod.LAST_WEEK:
        days_since_monday = now.weekday()
        this_week_start = today_start - timedelta(days=days_since_monday)
        start = this_week_start - timedelta(days=7)
        end = this_week_start
    elif period == TimePeriod.THIS_MONTH:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == TimePeriod.LAST_MONTH:
        first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = first_day_this_month - timedelta(days=1)
        start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = first_day_this_month
    elif period == TimePeriod.LAST_7_DAYS:
        start = now - timedelta(days=7)
        end = now
    elif period == TimePeriod.LAST_14_DAYS:
        start = now - timedelta(days=14)
        end = now
    elif period == TimePeriod.LAST_30_DAYS:
        start = now - timedelta(days=30)
        end = now
    else:
        raise ValueError(f"Unknown time period: {period}")
    
    return start, end

