
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User, UserRole
from app.crud.crud_registration import registration
from app.schemas.registration import Registration, RegistrationCreate, RegistrationUpdate

router = APIRouter()

@router.get("/", response_model=List[Registration])
def read_registrations(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve current user's registrations.
    """
    if current_user.role == UserRole.VISITOR:
        # Visitors see only their own registrations
        registrations = registration.get_visitor_registrations(
            db, visitor_id=current_user.id, skip=skip, limit=limit
        )
    else:
        # Admins and instructors can see all
        registrations = registration.get_multi(db, skip=skip, limit=limit)
    return registrations

@router.get("/group/{group_id}", response_model=List[Registration])
def read_group_registrations(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve registrations for a specific group.
    """
    # Check access permissions
    if current_user.role == UserRole.VISITOR:
        # Check if visitor is registered for this group
        visitor_registrations = registration.get_visitor_registrations(db, visitor_id=current_user.id)
        if not any(r.group_id == group_id for r in visitor_registrations):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this group's registrations",
            )
    
    registrations = registration.get_group_registrations(
        db, group_id=group_id, skip=skip, limit=limit
    )
    return registrations

@router.post("/", response_model=Registration)
def create_registration(
    *,
    db: Session = Depends(deps.get_db),
    registration_in: RegistrationCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new registration for current user.
    """
    # Only visitors can register
    if current_user.role != UserRole.VISITOR:
        raise HTTPException(
            status_code=400,
            detail="Only visitors can register for groups",
        )
    
    try:
        registration_obj = registration.create_with_visitor(
            db, obj_in=registration_in, visitor_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    
    return registration_obj

@router.post("/admin/{visitor_id}", response_model=Registration)
def create_registration_admin(
    *,
    db: Session = Depends(deps.get_db),
    visitor_id: int,
    registration_in: RegistrationCreate,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Admin endpoint to create registration for any visitor.
    """
    # Verify visitor exists
    visitor = db.query(User).filter(User.id == visitor_id, User.role == UserRole.VISITOR).first()
    if not visitor:
        raise HTTPException(
            status_code=404,
            detail="Visitor not found",
        )
    
    try:
        registration_obj = registration.create_with_visitor(
            db, obj_in=registration_in, visitor_id=visitor_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    
    return registration_obj

@router.delete("/{group_id}", response_model=dict)
def cancel_registration(
    *,
    db: Session = Depends(deps.get_db),
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancel user's registration for a group.
    """
    success = registration.cancel_registration(
        db, visitor_id=current_user.id, group_id=group_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Registration not found",
        )
    
    return {"success": True, "message": "Registration cancelled successfully"}

@router.put("/{registration_id}/attendance", response_model=Registration)
def update_attendance(
    *,
    db: Session = Depends(deps.get_db),
    registration_id: int,
    attended: bool,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update attendance status for a registration.
    Only instructors and admins can update attendance.
    """
    if current_user.role == UserRole.VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    registration_obj = registration.get(db, id=registration_id)
    if not registration_obj:
        raise HTTPException(
            status_code=404,
            detail="Registration not found",
        )
    
    # If instructor, check if they're assigned to this group
    if current_user.role == UserRole.INSTRUCTOR:
        group_obj = db.query(Group).filter(Group.id == registration_obj.group_id).first()
        if group_obj.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized for this group",
            )
    
    return registration.update_attendance(db, registration_id=registration_id, attended=attended)
