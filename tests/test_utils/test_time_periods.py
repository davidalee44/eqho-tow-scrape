"""Tests for time period utilities"""
import pytest
from datetime import datetime, timedelta
from app.utils.time_periods import get_time_period_range, TimePeriod


def test_get_time_period_today():
    """Test today time period"""
    start, end = get_time_period_range(TimePeriod.TODAY)
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    assert start == today_start
    assert end <= now
    assert (end - start).total_seconds() < 86400  # Less than 24 hours


def test_get_time_period_yesterday():
    """Test yesterday time period"""
    start, end = get_time_period_range(TimePeriod.YESTERDAY)
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    
    assert start == yesterday_start
    assert end == today_start


def test_get_time_period_last_7_days():
    """Test last 7 days time period"""
    start, end = get_time_period_range(TimePeriod.LAST_7_DAYS)
    
    now = datetime.utcnow()
    expected_start = now - timedelta(days=7)
    
    assert (end - start).days == 7
    assert start >= expected_start - timedelta(seconds=1)  # Allow 1 second tolerance
    assert end <= now


def test_get_time_period_last_30_days():
    """Test last 30 days time period"""
    start, end = get_time_period_range(TimePeriod.LAST_30_DAYS)
    
    assert (end - start).days == 30


def test_get_time_period_invalid():
    """Test invalid time period raises error"""
    with pytest.raises(ValueError):
        get_time_period_range("invalid_period")

