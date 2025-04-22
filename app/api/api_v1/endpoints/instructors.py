
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api import deps
from app.models.user import User, UserRole
from app.models.instructor_preference import DayOfWeek
from app.crud.crud_instructor import instructor_schedule, instructor_preference, instructor
from app.crud.crud_group import group
from app.schemas.instructor import (
    InstructorSchedule, InstructorScheduleCreate, InstructorScheduleUpdate,
    InstructorPreference, InstructorPreferenceCreate, InstructorPreferenceUpdate
)
from app.schemas.group import GroupList
from app.core.config import settings

router = APIRouter()

@router.get("/me/schedule", response_model=List[InstructorSchedule])
def read_instructor_schedule(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Retrieve current instructor's schedule.
    """
    schedules = instructor_schedule.get_instructor_schedule(
        db, instructor_id=current_user.id, skip=skip, limit=limit
    )
    return schedules

@router.get("/me/groups", response_model=List[GroupList])
def read_instructor_groups(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Retrieve groups assigned to current instructor.
    """
    groups = group.get_instructor_groups(
        db, instructor_id=current_user.id, skip=skip, limit=limit
    )
    return groups

@router.get("/me/hours", response_model=dict)
def read_instructor_hours(
    db: Session = Depends(deps.get_db),
    start_date: datetime = None,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Get summary of instructor's scheduled hours for the current week.
    """
    if not start_date:
        # Get start of current week (Monday)
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
    
    hours = instructor.get_instructor_hours_in_week(
        db, instructor_id=current_user.id, start_date=start_date
    )
    
    return {
        "current_hours": hours,
        "min_required": settings.INSTRUCTOR_MIN_HOURS_PER_WEEK,
        "max_allowed": settings.INSTRUCTOR_MAX_HOURS_PER_WEEK,
        "week_starting": start_date,
        "week_ending": start_date + timedelta(days=6),
        "is_underloaded": hours < settings.INSTRUCTOR_MIN_HOURS_PER_WEEK,
        "is_overloaded": hours > settings.INSTRUCTOR_MAX_HOURS_PER_WEEK,
    }

@router.get("/me/preferences", response_model=List[InstructorPreference])
def read_instructor_preferences(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Retrieve current instructor's preferred working hours.
    """
    preferences = instructor_preference.get_instructor_preferences(
        db, instructor_id=current_user.id
    )
    return preferences

@router.post("/me/preferences", response_model=InstructorPreference)
def create_instructor_preference(
    *,
    db: Session = Depends(deps.get_db),
    preference_in: InstructorPreferenceCreate,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Create new preferred working hours for current instructor.
    """
    preference = instructor_preference.create_for_instructor(
        db, obj_in=preference_in, instructor_id=current_user.id
    )
    return preference

@router.put("/me/preferences/{preference_id}", response_model=InstructorPreference)
def update_instructor_preference(
    *,
    db: Session = Depends(deps.get_db),
    preference_id: int,
    preference_in: InstructorPreferenceUpdate,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Update instructor's preference.
    """
    preference = instructor_preference.get(db, id=preference_id)
    if not preference or preference.instructor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Preference not found")
    
    preference = instructor_preference.update(
        db, db_obj=preference, obj_in=preference_in
    )
    return preference

@router.delete("/me/preferences/{preference_id}", response_model=dict)
def delete_instructor_preference(
    *,
    db: Session = Depends(deps.get_db),
    preference_id: int,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Delete instructor's preference.
    """
    preference = instructor_preference.get(db, id=preference_id)
    if not preference or preference.instructor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Preference not found")
    
    instructor_preference.remove(db, id=preference_id)
    return {"success": True}

@router.delete("/me/preferences", response_model=dict)
def clear_instructor_preferences(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Clear all preferences for current instructor.
    """
    success = instructor_preference.clear_instructor_preferences(
        db, instructor_id=current_user.id
    )
    return {"success": success}

# Admin routes for instructor management
@router.get("/{instructor_id}/hours", response_model=dict)
def read_instructor_hours_admin(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    start_date: datetime = None,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Admin endpoint to check an instructor's hours.
    """
    # Verify instructor exists
    instructor_user = db.query(User).filter(
        User.id == instructor_id, User.role == UserRole.INSTRUCTOR
    ).first()
    if not instructor_user:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    if not start_date:
        # Get start of current week (Monday)
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
    
    hours = instructor.get_instructor_hours_in_week(
        db, instructor_id=instructor_id, start_date=start_date
    )
    
    return {
        "instructor_id": instructor_id,
        "instructor_name": instructor_user.full_name,
        "current_hours": hours,
        "min_required": settings.INSTRUCTOR_MIN_HOURS_PER_WEEK,
        "max_allowed": settings.INSTRUCTOR_MAX_HOURS_PER_WEEK,
        "week_starting": start_date,
        "week_ending": start_date + timedelta(days=6),
        "is_underloaded": hours < settings.INSTRUCTOR_MIN_HOURS_PER_WEEK,
        "is_overloaded": hours > settings.INSTRUCTOR_MAX_HOURS_PER_WEEK,
    }

@router.get("/{instructor_id}/preferences", response_model=List[InstructorPreference])
def read_instructor_preferences_admin(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Admin endpoint to view an instructor's preferences.
    """
    # Verify instructor exists
    instructor_user = db.query(User).filter(
        User.id == instructor_id, User.role == UserRole.INSTRUCTOR
    ).first()
    if not instructor_user:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    preferences = instructor_preference.get_instructor_preferences(
        db, instructor_id=instructor_id
    )
    return preferences
