
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, extract, case

from app.crud.base import CRUDBase
from app.models.instructor_schedule import InstructorSchedule
from app.models.instructor_preference import InstructorPreference, DayOfWeek
from app.models.user import User, UserRole
from app.models.group import Group
from app.schemas.instructor import InstructorScheduleCreate, InstructorScheduleUpdate
from app.schemas.instructor import InstructorPreferenceCreate, InstructorPreferenceUpdate
from app.core.config import settings
from datetime import datetime, timedelta, time

class CRUDInstructorSchedule(CRUDBase[InstructorSchedule, InstructorScheduleCreate, InstructorScheduleUpdate]):
    def create_for_instructor(
        self, db: Session, *, obj_in: InstructorScheduleCreate, instructor_id: int
    ) -> InstructorSchedule:
        db_obj = InstructorSchedule(
            instructor_id=instructor_id,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_instructor_schedule(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[InstructorSchedule]:
        return db.query(InstructorSchedule).filter(
            InstructorSchedule.instructor_id == instructor_id
        ).order_by(InstructorSchedule.start_time).offset(skip).limit(limit).all()
    
    def get_instructor_schedule_by_date_range(
        self, db: Session, *, instructor_id: int, start_date: datetime, end_date: datetime
    ) -> List[InstructorSchedule]:
        return db.query(InstructorSchedule).filter(
            InstructorSchedule.instructor_id == instructor_id,
            InstructorSchedule.start_time >= start_date,
            InstructorSchedule.end_time <= end_date
        ).order_by(InstructorSchedule.start_time).all()


class CRUDInstructorPreference(CRUDBase[InstructorPreference, InstructorPreferenceCreate, InstructorPreferenceUpdate]):
    def create_for_instructor(
        self, db: Session, *, obj_in: InstructorPreferenceCreate, instructor_id: int
    ) -> InstructorPreference:
        db_obj = InstructorPreference(
            instructor_id=instructor_id,
            day_of_week=obj_in.day_of_week,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_instructor_preferences(
        self, db: Session, *, instructor_id: int
    ) -> List[InstructorPreference]:
        return db.query(InstructorPreference).filter(
            InstructorPreference.instructor_id == instructor_id
        ).all()
    
    def clear_instructor_preferences(
        self, db: Session, *, instructor_id: int
    ) -> bool:
        db.query(InstructorPreference).filter(
            InstructorPreference.instructor_id == instructor_id
        ).delete()
        db.commit()
        return True


class CRUDInstructor:
    def get_instructor_hours_in_week(
        self, db: Session, *, instructor_id: int, start_date: datetime
    ) -> float:
        """Calculate instructor hours for a week starting from start_date"""
        end_date = start_date + timedelta(days=7)
        
        # Get all groups for the instructor in the date range
        groups = db.query(Group).filter(
            Group.instructor_id == instructor_id,
            Group.start_time >= start_date,
            Group.end_time <= end_date
        ).all()
        
        total_hours = 0
        for group in groups:
            delta = (group.end_time - group.start_time).total_seconds() / 3600
            total_hours += delta
        
        return total_hours
    
    def get_available_instructors_for_group(
        self, db: Session, *, group_start: datetime, group_end: datetime, 
        group_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[Tuple[User, bool, bool]]:
        """
        Get instructors available for a group time slot, with info about:
        - Whether they're overloaded (exceeding max hours)
        - Whether the time matches their preferences
        
        Returns a list of tuples (instructor, is_overloaded, matches_preferences)
        """
        instructors = db.query(User).filter(
            User.role == UserRole.INSTRUCTOR,
            User.is_active == True
        ).all()
        
        results = []
        start_of_week = group_start - timedelta(days=group_start.weekday())
        
        for instructor in instructors:
            # Check current scheduled hours
            current_hours = self.get_instructor_hours_in_week(
                db, instructor_id=instructor.id, start_date=start_of_week
            )
            
            # Get potential new hours if assigned to this group
            group_hours = (group_end - group_start).total_seconds() / 3600
            total_hours = current_hours + group_hours
            
            # Check if instructor would be overloaded with this additional group
            is_overloaded = (
                total_hours > settings.INSTRUCTOR_MAX_HOURS_PER_WEEK or
                total_hours < settings.INSTRUCTOR_MIN_HOURS_PER_WEEK
            )
            
            # Check for time conflicts with existing groups
            conflicts = db.query(Group).filter(
                Group.instructor_id == instructor.id,
                or_(
                    and_(
                        Group.start_time <= group_start,
                        Group.end_time > group_start
                    ),
                    and_(
                        Group.start_time < group_end,
                        Group.end_time >= group_end
                    ),
                    and_(
                        Group.start_time >= group_start,
                        Group.end_time <= group_end
                    )
                )
            )
            
            # Exclude the current group being edited if group_id is provided
            if group_id:
                conflicts = conflicts.filter(Group.id != group_id)
            
            if conflicts.first():
                # Skip this instructor if there's a time conflict
                continue
            
            # Check if the time matches instructor preferences
            day_of_week = DayOfWeek(group_start.strftime('%A').lower())
            group_start_time = group_start.time()
            group_end_time = group_end.time()
            
            preferences = db.query(InstructorPreference).filter(
                InstructorPreference.instructor_id == instructor.id,
                InstructorPreference.day_of_week == day_of_week
            ).all()
            
            matches_preferences = False
            if preferences:
                for pref in preferences:
                    if pref.start_time <= group_start_time and pref.end_time >= group_end_time:
                        matches_preferences = True
                        break
            
            # Add to results if not overloaded or if we're just checking preferences
            if not is_overloaded:
                results.append((instructor, is_overloaded, matches_preferences))
        
        # Apply pagination
        return results[skip:skip+limit]


instructor_schedule = CRUDInstructorSchedule(InstructorSchedule)
instructor_preference = CRUDInstructorPreference(InstructorPreference)
instructor = CRUDInstructor()
