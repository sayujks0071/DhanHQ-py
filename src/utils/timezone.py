"""
Timezone utilities for the Liquid F&O Trading System.
"""

from datetime import datetime, time, timezone, timedelta
from typing import Optional
import pytz


class ISTTimezone:
    """Indian Standard Time timezone utilities."""
    
    IST = pytz.timezone('Asia/Kolkata')
    
    @classmethod
    def now(cls) -> datetime:
        """Get current time in IST."""
        return datetime.now(cls.IST)
    
    @classmethod
    def utc_to_ist(cls, utc_dt: datetime) -> datetime:
        """Convert UTC datetime to IST."""
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        return utc_dt.astimezone(cls.IST)
    
    @classmethod
    def ist_to_utc(cls, ist_dt: datetime) -> datetime:
        """Convert IST datetime to UTC."""
        if ist_dt.tzinfo is None:
            ist_dt = cls.IST.localize(ist_dt)
        return ist_dt.astimezone(timezone.utc)
    
    @classmethod
    def is_market_hours(cls, dt: Optional[datetime] = None) -> bool:
        """Check if current time is within market hours."""
        if dt is None:
            dt = cls.now()
        elif dt.tzinfo is None:
            dt = cls.IST.localize(dt)
        
        current_time = dt.time()
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        return market_open <= current_time <= market_close
    
    @classmethod
    def is_pre_market(cls, dt: Optional[datetime] = None) -> bool:
        """Check if current time is pre-market hours."""
        if dt is None:
            dt = cls.now()
        elif dt.tzinfo is None:
            dt = cls.IST.localize(dt)
        
        current_time = dt.time()
        pre_open = time(9, 0)
        market_open = time(9, 15)
        
        return pre_open <= current_time < market_open
    
    @classmethod
    def is_after_market(cls, dt: Optional[datetime] = None) -> bool:
        """Check if current time is after market hours."""
        if dt is None:
            dt = cls.now()
        elif dt.tzinfo is None:
            dt = cls.IST.localize(dt)
        
        current_time = dt.time()
        market_close = time(15, 30)
        
        return current_time > market_close
    
    @classmethod
    def get_next_market_open(cls, dt: Optional[datetime] = None) -> datetime:
        """Get next market open time."""
        if dt is None:
            dt = cls.now()
        elif dt.tzinfo is None:
            dt = cls.IST.localize(dt)
        
        # If it's weekend, get next Monday
        if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            days_ahead = 7 - dt.weekday()  # Monday = 0
            dt = dt + timedelta(days=days_ahead)
        
        # Set to market open time
        market_open = dt.replace(hour=9, minute=15, second=0, microsecond=0)
        
        # If market is already open today, get next day
        if cls.is_market_hours(dt):
            market_open += timedelta(days=1)
        
        return market_open
    
    @classmethod
    def get_market_close_today(cls, dt: Optional[datetime] = None) -> datetime:
        """Get market close time for today."""
        if dt is None:
            dt = cls.now()
        elif dt.tzinfo is None:
            dt = cls.IST.localize(dt)
        
        return dt.replace(hour=15, minute=30, second=0, microsecond=0)
    
    @classmethod
    def get_trading_days_until(cls, end_date: datetime) -> int:
        """Get number of trading days until end_date."""
        if end_date.tzinfo is None:
            end_date = cls.IST.localize(end_date)
        
        current = cls.now()
        trading_days = 0
        
        while current.date() < end_date.date():
            if current.weekday() < 5:  # Monday to Friday
                trading_days += 1
            current += timedelta(days=1)
        
        return trading_days
    
    @classmethod
    def is_weekly_expiry_day(cls, dt: Optional[datetime] = None) -> bool:
        """Check if current day is weekly expiry day (Thursday)."""
        if dt is None:
            dt = cls.now()
        elif dt.tzinfo is None:
            dt = cls.IST.localize(dt)
        
        return dt.weekday() == 3  # Thursday = 3
    
    @classmethod
    def get_next_weekly_expiry(cls, dt: Optional[datetime] = None) -> datetime:
        """Get next weekly expiry date (Thursday)."""
        if dt is None:
            dt = cls.now()
        elif dt.tzinfo is None:
            dt = cls.IST.localize(dt)
        
        # Calculate days until next Thursday
        days_ahead = (3 - dt.weekday()) % 7
        if days_ahead == 0 and dt.time() > time(15, 30):
            days_ahead = 7  # If market is closed, get next Thursday
        
        return dt + timedelta(days=days_ahead)
    
    @classmethod
    def get_monthly_expiry(cls, year: int, month: int) -> datetime:
        """Get monthly expiry date (last Thursday of the month)."""
        # Get last day of month
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Find last Thursday
        while last_day.weekday() != 3:  # Thursday = 3
            last_day -= timedelta(days=1)
        
        return cls.IST.localize(last_day.replace(hour=15, minute=30, second=0, microsecond=0))
