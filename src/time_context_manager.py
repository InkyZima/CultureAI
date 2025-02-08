"""Time Context Manager for the Cultural AI Companion.

This module manages time-based context for the chat system, enabling the AI to make
time-appropriate suggestions and maintain natural conversation flow based on time of day.
"""

from datetime import datetime, time
from dataclasses import dataclass
from typing import Optional
from zoneinfo import ZoneInfo

@dataclass
class TimeContext:
    """Represents the current time context for the conversation."""
    current_time: datetime
    time_of_day: str  # 'early_morning', 'morning', 'afternoon', 'evening', 'night'
    is_weekend: bool
    timezone: ZoneInfo

class TimeContextManager:
    """Manages time-based context for the chat system."""
    
    # Time ranges for different parts of the day
    TIME_RANGES = {
        'early_morning': (time(4, 0), time(7, 0)),    # 4:00 AM - 7:00 AM
        'morning': (time(7, 0), time(12, 0)),         # 7:00 AM - 12:00 PM
        'afternoon': (time(12, 0), time(17, 0)),      # 12:00 PM - 5:00 PM
        'evening': (time(17, 0), time(22, 0)),        # 5:00 PM - 10:00 PM
        'night': (time(22, 0), time(4, 0))           # 10:00 PM - 4:00 AM
    }

    def __init__(self, timezone: Optional[str] = None):
        """Initialize the TimeContextManager.
        
        Args:
            timezone: Optional timezone string. If not provided, uses system timezone.
        """
        self.timezone = ZoneInfo(timezone) if timezone else ZoneInfo('UTC')
    
    def _determine_time_of_day(self, current_time: datetime) -> str:
        """Determine the time of day based on the current time.
        
        Args:
            current_time: Current datetime object
            
        Returns:
            str: One of 'early_morning', 'morning', 'afternoon', 'evening', 'night'
        """
        current_time_obj = current_time.time()
        
        # Special handling for night time which crosses midnight
        if (current_time_obj >= self.TIME_RANGES['night'][0] or 
            current_time_obj < self.TIME_RANGES['night'][1]):
            return 'night'
            
        # Check other time ranges
        for time_of_day, (start, end) in self.TIME_RANGES.items():
            if time_of_day != 'night' and start <= current_time_obj < end:
                return time_of_day
                
        return 'night'  # Default fallback
    
    def get_time_context(self, current_time: datetime) -> TimeContext:
        """Get the current time context.
        
        Args:
            current_time: Current datetime object with timezone info
            
        Returns:
            TimeContext: Current time context object
        """
        # Ensure the datetime has timezone info
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=self.timezone)
            
        time_of_day = self._determine_time_of_day(current_time)
        is_weekend = current_time.weekday() >= 5  # 5=Saturday, 6=Sunday
        
        return TimeContext(
            current_time=current_time,
            time_of_day=time_of_day,
            is_weekend=is_weekend,
            timezone=self.timezone
        )
    
    def get_time_appropriate_greeting(self, time_context: TimeContext) -> str:
        """Get a time-appropriate greeting based on the time context.
        
        Args:
            time_context: Current time context
            
        Returns:
            str: Appropriate greeting for the time of day
        """
        greetings = {
            'early_morning': "Good early morning",
            'morning': "Good morning",
            'afternoon': "Good afternoon",
            'evening': "Good evening",
            'night': "Good night"
        }
        return greetings.get(time_context.time_of_day, "Hello")
    
    def get_time_context_prompt(self, time_context: TimeContext) -> str:
        """Generate a system prompt addition based on time context.
        
        Args:
            time_context: Current time context
            
        Returns:
            str: Time-aware context for system prompt
        """
        day_type = "weekend" if time_context.is_weekend else "weekday"
        
        context_prompts = {
            'early_morning': (
                "It's early morning, a time for starting the day mindfully. "
                "Consider morning routines, meditation, or light exercise."
            ),
            'morning': (
                "It's morning time, ideal for productivity and important tasks. "
                "Consider breakfast, daily planning, and engaging activities."
            ),
            'afternoon': (
                "It's afternoon, a time for maintaining momentum and taking breaks. "
                "Consider lunch, work progress, and staying energized."
            ),
            'evening': (
                "It's evening, time to wind down and reflect. "
                "Consider dinner, daily review, and relaxation activities."
            ),
            'night': (
                "It's nighttime, perfect for rest and preparation. "
                "Consider tomorrow's planning, sleep routine, and peaceful activities."
            )
        }
        
        base_prompt = context_prompts.get(time_context.time_of_day, "")
        return f"{base_prompt} As it's a {day_type}, adjust activities accordingly."
