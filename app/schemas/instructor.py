
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, time
from app.models.instructor_preference import DayOfWeek

# Instructor schedule
class InstructorScheduleBase(BaseModel):
    start_time: datetime
    end_time: datetime

class InstructorScheduleCreate(InstructorScheduleBase):
    pass

class InstructorScheduleUpdate(InstructorScheduleBase):
    pass

class InstructorScheduleInDB(InstructorScheduleBase):
    id: int
    instructor_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class InstructorSchedule(InstructorScheduleInDB):
    pass

# Instructor preferences
class InstructorPreferenceBase(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time

class InstructorPreferenceCreate(InstructorPreferenceBase):
    pass

class InstructorPreferenceUpdate(InstructorPreferenceBase):
    pass

class InstructorPreferenceInDB(InstructorPreferenceBase):
    id: int
    instructor_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class InstructorPreference(InstructorPreferenceInDB):
    pass

# Instructor availability info for admin
class InstructorAvailability(BaseModel):
    instructor_id: int
    full_name: str
    email: str
    current_hours_scheduled: float
    min_hours_required: int
    max_hours_allowed: int
    is_overloaded: bool
    matches_preferences: bool
    
    class Config:
        orm_mode = True
