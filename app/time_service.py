"""
Beijing Time Service for Customer Support

Handles business hours logic for live chat support availability.
Beijing timezone: UTC+8
Business hours: 8:00 AM - 8:00 PM (Beijing time)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any

class BeijingTimeService:
    """Service for managing Beijing timezone and business hours"""
    
    # Beijing timezone offset: UTC+8
    BEIJING_TIMEZONE = timezone(timedelta(hours=8))
    
    # Business hours in 24-hour format
    BUSINESS_START_HOUR = 8  # 8:00 AM
    BUSINESS_END_HOUR = 20   # 8:00 PM (20:00)
    
    def __init__(self):
        print("🕐 Initialized Beijing Time Service")
    
    def get_beijing_time(self) -> datetime:
        """
        Get current Beijing time
        
        Returns:
            Current datetime in Beijing timezone
        """
        return datetime.now(self.BEIJING_TIMEZONE)
    
    def is_business_hours(self) -> bool:
        """
        Check if current Beijing time is within business hours
        
        Returns:
            True if live support is available, False otherwise
        """
        beijing_now = self.get_beijing_time()
        current_hour = beijing_now.hour
        
        return self.BUSINESS_START_HOUR <= current_hour < self.BUSINESS_END_HOUR
    
    def get_business_status(self) -> Dict[str, Any]:
        """
        Get comprehensive business hours status
        
        Returns:
            Dictionary with current status and timing information
        """
        beijing_now = self.get_beijing_time()
        is_online = self.is_business_hours()
        
        return {
            "is_online": is_online,
            "beijing_time": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
            "beijing_hour": beijing_now.hour,
            "business_hours": f"{self.BUSINESS_START_HOUR:02d}:00-{self.BUSINESS_END_HOUR:02d}:00 Beijing Time",
            "status_message": self._get_status_message(beijing_now, is_online)
        }
    
    def _get_status_message(self, beijing_time: datetime, is_online: bool) -> str:
        """
        Generate user-friendly status message
        
        Args:
            beijing_time: Current Beijing time
            is_online: Whether support is currently available
            
        Returns:
            Human-readable status message
        """
        if is_online:
            return "Live support is available now!"
        
        current_hour = beijing_time.hour
        
        if current_hour < self.BUSINESS_START_HOUR:
            # Before business hours
            hours_until_open = self.BUSINESS_START_HOUR - current_hour
            return f"Live support opens in {hours_until_open} hour{'s' if hours_until_open != 1 else ''} (8:00 AM Beijing time)"
        else:
            # After business hours
            hours_until_open = (24 - current_hour) + self.BUSINESS_START_HOUR
            return f"Live support opens in {hours_until_open} hour{'s' if hours_until_open != 1 else ''} (8:00 AM Beijing time tomorrow)"
    
    def get_next_business_hours(self) -> Dict[str, Any]:
        """
        Get information about when support will next be available
        
        Returns:
            Dictionary with next availability timing
        """
        beijing_now = self.get_beijing_time()
        
        if self.is_business_hours():
            # Currently online, next closure
            today_end = beijing_now.replace(hour=self.BUSINESS_END_HOUR, minute=0, second=0, microsecond=0)
            hours_until_close = (today_end - beijing_now).total_seconds() / 3600
            
            return {
                "currently_online": True,
                "hours_until_change": hours_until_close,
                "next_change": "closes",
                "next_change_time": today_end.strftime("%H:%M Beijing time")
            }
        else:
            # Currently offline, next opening
            current_hour = beijing_now.hour
            
            if current_hour < self.BUSINESS_START_HOUR:
                # Same day opening
                today_start = beijing_now.replace(hour=self.BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
                hours_until_open = (today_start - beijing_now).total_seconds() / 3600
                next_open_time = today_start
            else:
                # Next day opening
                tomorrow = beijing_now + timedelta(days=1)
                tomorrow_start = tomorrow.replace(hour=self.BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
                hours_until_open = (tomorrow_start - beijing_now).total_seconds() / 3600
                next_open_time = tomorrow_start
            
            return {
                "currently_online": False,
                "hours_until_change": hours_until_open,
                "next_change": "opens",
                "next_change_time": next_open_time.strftime("%H:%M Beijing time")
            }
    
    def format_business_hours_display(self) -> str:
        """
        Format business hours for display to users
        
        Returns:
            Formatted business hours string
        """
        return f"Live Support Hours: {self.BUSINESS_START_HOUR:02d}:00 - {self.BUSINESS_END_HOUR:02d}:00 Beijing Time"
    
    def is_weekend(self) -> bool:
        """
        Check if current Beijing time is weekend
        Note: This can be extended later if weekend support differs
        
        Returns:
            True if it's weekend in Beijing
        """
        beijing_now = self.get_beijing_time()
        # 5 = Saturday, 6 = Sunday
        return beijing_now.weekday() >= 5

# Global instance
beijing_time_service = BeijingTimeService()