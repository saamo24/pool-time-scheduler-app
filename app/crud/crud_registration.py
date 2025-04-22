
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.registration import Registration
from app.models.user import User, Gender
from app.models.group import Group
from app.schemas.registration import RegistrationCreate, RegistrationUpdate

class CRUDRegistration(CRUDBase[Registration, RegistrationCreate, RegistrationUpdate]):
    def create_with_visitor(
        self, db: Session, *, obj_in: RegistrationCreate, visitor_id: int
    ) -> Registration:
        # First check if the visitor is already registered for this group
        existing = db.query(Registration).filter(
            Registration.visitor_id == visitor_id,
            Registration.group_id == obj_in.group_id
        ).first()
        
        if existing:
            return existing
        
        # Check if the group has capacity
        group = db.query(Group).options(
            joinedload(Group.registrations).joinedload("visitor")
        ).filter(Group.id == obj_in.group_id).first()
        
        if not group:
            raise ValueError("Group not found")
        
        if group.is_full:
            raise ValueError("Group is at full capacity")
        
        # Get visitor's gender
        visitor = db.query(User).filter(User.id == visitor_id).first()
        if not visitor:
            raise ValueError("Visitor not found")
        
        # Check gender-specific capacity
        if visitor.gender == Gender.MALE and group.is_male_full:
            raise ValueError("No more spaces available for male visitors")
        elif visitor.gender == Gender.FEMALE and group.is_female_full:
            raise ValueError("No more spaces available for female visitors")
        
        # Create registration
        db_obj = Registration(
            visitor_id=visitor_id,
            group_id=obj_in.group_id,
            attended=obj_in.attended
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_visitor_registrations(
        self, db: Session, *, visitor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Registration]:
        return db.query(Registration).options(
            joinedload(Registration.group).joinedload("instructor")
        ).filter(
            Registration.visitor_id == visitor_id
        ).offset(skip).limit(limit).all()
    
    def get_group_registrations(
        self, db: Session, *, group_id: int, skip: int = 0, limit: int = 100
    ) -> List[Registration]:
        return db.query(Registration).options(
            joinedload(Registration.visitor)
        ).filter(
            Registration.group_id == group_id
        ).offset(skip).limit(limit).all()
    
    def cancel_registration(
        self, db: Session, *, visitor_id: int, group_id: int
    ) -> bool:
        registration = db.query(Registration).filter(
            Registration.visitor_id == visitor_id,
            Registration.group_id == group_id
        ).first()
        
        if registration:
            db.delete(registration)
            db.commit()
            return True
        return False
    
    def update_attendance(
        self, db: Session, *, registration_id: int, attended: bool
    ) -> Registration:
        registration = self.get(db, id=registration_id)
        if registration:
            registration.attended = attended
            db.add(registration)
            db.commit()
            db.refresh(registration)
        return registration


registration = CRUDRegistration(Registration)
