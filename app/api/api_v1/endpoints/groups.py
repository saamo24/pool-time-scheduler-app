
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User, Gender
from app.crud.crud_group import group
from app.crud.crud_instructor import instructor
from app.schemas.group import Group, GroupCreate, GroupUpdate, GroupList
from app.schemas.instructor import InstructorAvailability
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=List[GroupList])
def read_groups(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve groups.
    """
    groups = group.get_multi_with_details(db, skip=skip, limit=limit)
    return groups

@router.get("/upcoming", response_model=List[GroupList])
def read_upcoming_groups(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve upcoming groups.
    """
    groups = group.get_upcoming_groups(db, skip=skip, limit=limit)
    return groups

@router.get("/available", response_model=List[GroupList])
def read_available_groups(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve groups available for the current visitor to join.
    """
    if not current_user.gender:
        raise HTTPException(status_code=400, detail="User gender is required to check availability")
    
    groups = group.get_visitor_available_groups(
        db, visitor_id=current_user.id, gender=current_user.gender, skip=skip, limit=limit
    )
    return groups

@router.post("/", response_model=Group)
def create_group(
    *,
    db: Session = Depends(deps.get_db),
    group_in: GroupCreate,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Create new group.
    """
    # Validate instructor if provided
    if group_in.instructor_id:
        instructor_user = db.query(User).filter(User.id == group_in.instructor_id).first()
        if not instructor_user or instructor_user.role != "instructor":
            raise HTTPException(status_code=400, detail="Invalid instructor")
    
    group_obj = group.create_with_instructor(db, obj_in=group_in)
    return group_obj

@router.get("/{group_id}", response_model=Group)
def read_group(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get group by ID.
    """
    group_obj = group.get_with_details(db, id=group_id)
    if not group_obj:
        raise HTTPException(status_code=404, detail="Group not found")
    return group_obj

@router.put("/{group_id}", response_model=Group)
def update_group(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    group_in: GroupUpdate,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Update a group.
    """
    group_obj = group.get(db, id=group_id)
    if not group_obj:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Validate instructor if provided
    if group_in.instructor_id:
        instructor_user = db.query(User).filter(User.id == group_in.instructor_id).first()
        if not instructor_user or instructor_user.role != "instructor":
            raise HTTPException(status_code=400, detail="Invalid instructor")
    
    group_obj = group.update(db, db_obj=group_obj, obj_in=group_in)
    return group_obj

@router.get("/{group_id}/available-instructors", response_model=List[InstructorAvailability])
def read_available_instructors(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = Query(None, description="Sort by: 'hours_scheduled', 'preference_match'"),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Get available instructors for a group, with their current load and preference match.
    """
    group_obj = group.get(db, id=group_id)
    if not group_obj:
        raise HTTPException(status_code=404, detail="Group not found")
    
    available_instructors = instructor.get_available_instructors_for_group(
        db, group_start=group_obj.start_time, group_end=group_obj.end_time, 
        group_id=group_id, skip=skip, limit=limit
    )
    
    # Create response objects
    result = []
    for instr, is_overloaded, matches_preferences in available_instructors:
        result.append({
            "instructor_id": instr.id,
            "full_name": instr.full_name,
            "email": instr.email,
            "current_hours_scheduled": instructor.get_instructor_hours_in_week(
                db, instructor_id=instr.id, 
                start_date=group_obj.start_time - timedelta(days=group_obj.start_time.weekday())
            ),
            "min_hours_required": settings.INSTRUCTOR_MIN_HOURS_PER_WEEK,
            "max_hours_allowed": settings.INSTRUCTOR_MAX_HOURS_PER_WEEK,
            "is_overloaded": is_overloaded,
            "matches_preferences": matches_preferences
        })
    
    # Sort results if requested
    if sort_by == "hours_scheduled":
        result.sort(key=lambda x: x["current_hours_scheduled"])
    elif sort_by == "preference_match":
        result.sort(key=lambda x: (not x["matches_preferences"], x["current_hours_scheduled"]))
    
    return result

@router.put("/{group_id}/instructor/{instructor_id}", response_model=Group)
def update_group_instructor(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    instructor_id: int,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Update the instructor for a group.
    """
    # Validate instructor
    instructor_user = db.query(User).filter(User.id == instructor_id).first()
    if not instructor_user or instructor_user.role != "instructor":
        raise HTTPException(status_code=400, detail="Invalid instructor")
    
    group_obj = group.get(db, id=group_id)
    if not group_obj:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if instructor is available and not overloaded
    available_instructors = instructor.get_available_instructors_for_group(
        db, group_start=group_obj.start_time, group_end=group_obj.end_time, 
        group_id=group_id
    )
    
    valid_instructor_ids = [i[0].id for i in available_instructors if not i[1]]  # filter out overloaded
    if instructor_id not in valid_instructor_ids:
        raise HTTPException(
            status_code=400, 
            detail="Instructor is not available or would be overloaded by this assignment"
        )
    
    group_obj = group.update_instructor(db, group_id=group_id, new_instructor_id=instructor_id)
    return group_obj

@router.delete("/{group_id}/instructor", response_model=Group)
def remove_group_instructor(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Remove the instructor from a group.
    """
    group_obj = group.get(db, id=group_id)
    if not group_obj:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_obj = group.update_instructor(db, group_id=group_id, new_instructor_id=None)
    return group_obj
