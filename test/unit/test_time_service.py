"""
Test suite for BeijingTimeService

Tests business hours logic and timezone handling.
"""

import pytest
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.time_service import BeijingTimeService

class TestBeijingTimeService:
    """Test cases for BeijingTimeService"""
    
    def setup_method(self):
        """Set up test environment"""
        self.service = BeijingTimeService()
    
    def test_beijing_timezone_offset(self):
        """Test that Beijing timezone is correctly set to UTC+8"""
        expected_offset = timedelta(hours=8)
        assert self.service.BEIJING_TIMEZONE.utcoffset(None) == expected_offset
        print("✅ Beijing timezone offset is correct (UTC+8)")
    
    def test_business_hours_constants(self):
        """Test business hours constants"""
        assert self.service.BUSINESS_START_HOUR == 7  # 7 AM
        assert self.service.BUSINESS_END_HOUR == 18   # 6 PM (18:00)
        print("✅ Business hours constants: 7:00 AM - 6:00 PM")
    
    @patch('app.time_service.datetime')
    def test_business_hours_during_work_time(self, mock_datetime):
        """Test business hours check during work time"""
        # Mock Beijing time to 10:00 AM (within business hours)
        mock_beijing_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        assert self.service.is_business_hours() == True
        print("✅ 10:30 AM Beijing time -> Business hours: Online")
    
    @patch('app.time_service.datetime')
    def test_business_hours_before_work(self, mock_datetime):
        """Test business hours check before work time"""
        # Mock Beijing time to 6:00 AM (before business hours)
        mock_beijing_time = datetime(2024, 1, 15, 6, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        assert self.service.is_business_hours() == False
        print("✅ 6:00 AM Beijing time -> Before business hours: Offline")
    
    @patch('app.time_service.datetime')
    def test_business_hours_after_work(self, mock_datetime):
        """Test business hours check after work time"""
        # Mock Beijing time to 7:00 PM (after business hours)
        mock_beijing_time = datetime(2024, 1, 15, 19, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        assert self.service.is_business_hours() == False
        print("✅ 7:00 PM Beijing time -> After business hours: Offline")
    
    @patch('app.time_service.datetime')
    def test_business_hours_exactly_start(self, mock_datetime):
        """Test business hours at exactly start time"""
        # Mock Beijing time to exactly 7:00 AM
        mock_beijing_time = datetime(2024, 1, 15, 7, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        assert self.service.is_business_hours() == True
        print("✅ 7:00 AM Beijing time (start) -> Business hours: Online")
    
    @patch('app.time_service.datetime')
    def test_business_hours_exactly_end(self, mock_datetime):
        """Test business hours at exactly end time"""
        # Mock Beijing time to exactly 6:00 PM (18:00)
        mock_beijing_time = datetime(2024, 1, 15, 18, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        assert self.service.is_business_hours() == False
        print("✅ 6:00 PM Beijing time (end) -> After business hours: Offline")
    
    @patch('app.time_service.datetime')
    def test_get_business_status_online(self, mock_datetime):
        """Test get_business_status when online"""
        # Mock Beijing time to 2:30 PM (within business hours)
        mock_beijing_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        status = self.service.get_business_status()
        
        assert status["is_online"] == True
        assert status["beijing_hour"] == 14
        assert "2024-01-15 14:30:00" in status["beijing_time"]
        assert "07:00-18:00 Beijing Time" in status["business_hours"]
        assert "Live support is available now!" in status["status_message"]
        
        print("✅ Business status during online hours: Correct")
    
    @patch('app.time_service.datetime')
    def test_get_business_status_offline(self, mock_datetime):
        """Test get_business_status when offline"""
        # Mock Beijing time to 11:00 PM (after business hours)
        mock_beijing_time = datetime(2024, 1, 15, 23, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        status = self.service.get_business_status()
        
        assert status["is_online"] == False
        assert status["beijing_hour"] == 23
        assert "opens in" in status["status_message"]
        
        print("✅ Business status during offline hours: Correct")
    
    @patch('app.time_service.datetime')
    def test_status_message_before_hours(self, mock_datetime):
        """Test status message generation before business hours"""
        # Mock Beijing time to 5:00 AM
        mock_beijing_time = datetime(2024, 1, 15, 5, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        message = self.service._get_status_message(mock_beijing_time, False)
        
        assert "opens in 2 hours" in message
        assert "7:00 AM Beijing time" in message
        
        print("✅ Status message before hours: 'opens in 2 hours'")
    
    @patch('app.time_service.datetime')
    def test_status_message_after_hours(self, mock_datetime):
        """Test status message generation after business hours"""
        # Mock Beijing time to 8:00 PM
        mock_beijing_time = datetime(2024, 1, 15, 20, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        message = self.service._get_status_message(mock_beijing_time, False)
        
        assert "opens in 11 hours" in message
        assert "tomorrow" in message
        
        print("✅ Status message after hours: 'opens in 11 hours tomorrow'")
    
    def test_format_business_hours_display(self):
        """Test business hours display formatting"""
        display = self.service.format_business_hours_display()
        
        assert "Live Support Hours: 07:00 - 18:00 Beijing Time" == display
        
        print("✅ Business hours display format: Correct")
    
    @patch('app.time_service.datetime')
    def test_weekend_detection(self, mock_datetime):
        """Test weekend detection"""
        # Mock Saturday (weekday = 5)
        saturday = datetime(2024, 1, 13, 10, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)  
        mock_datetime.now.return_value = saturday
        
        assert self.service.is_weekend() == True
        
        # Mock Monday (weekday = 0)
        monday = datetime(2024, 1, 15, 10, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = monday
        
        assert self.service.is_weekend() == False
        
        print("✅ Weekend detection: Saturday=True, Monday=False")
    
    @patch('app.time_service.datetime')
    def test_next_business_hours_currently_online(self, mock_datetime):
        """Test next business hours when currently online"""
        # Mock 10:00 AM (2 hours until closing at 6 PM)
        mock_beijing_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=self.service.BEIJING_TIMEZONE)
        mock_datetime.now.return_value = mock_beijing_time
        
        next_hours = self.service.get_next_business_hours()
        
        assert next_hours["currently_online"] == True
        assert next_hours["next_change"] == "closes"
        assert abs(next_hours["hours_until_change"] - 8.0) < 0.1  # About 8 hours until 6 PM
        
        print("✅ Next business hours when online: Closes in 8 hours")

def run_time_service_tests():
    """Run all time service tests"""
    print("🧪 Testing BeijingTimeService...")
    print("=" * 50)
    
    test_service = TestBeijingTimeService()
    test_service.setup_method()
    
    try:
        # Run all tests
        test_service.test_beijing_timezone_offset()
        test_service.test_business_hours_constants()
        test_service.test_business_hours_during_work_time()
        test_service.test_business_hours_before_work()
        test_service.test_business_hours_after_work()
        test_service.test_business_hours_exactly_start()
        test_service.test_business_hours_exactly_end()
        test_service.test_get_business_status_online()
        test_service.test_get_business_status_offline()
        test_service.test_status_message_before_hours()
        test_service.test_status_message_after_hours()
        test_service.test_format_business_hours_display()
        test_service.test_weekend_detection()
        test_service.test_next_business_hours_currently_online()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TIME SERVICE TESTS PASSED!")
        print("✅ Beijing timezone: CORRECT")
        print("✅ Business hours logic: WORKING")
        print("✅ Status messages: ACCURATE")
        print("✅ Weekend detection: WORKING")
        print("✅ Time service ready for production!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ Time service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_time_service_tests()
    sys.exit(0 if success else 1)