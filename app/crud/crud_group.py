
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, extract

from app.crud.base import CRUDBase
from app.models.group import Group
from app.models.user import User, UserRole
from app.schemas.group import GroupCreate, GroupUpdate
from datetime import datetime, timedelta

class CRUDGroup(CRUDBase[Group, GroupCreate, GroupUpdate]):
    def create_with_instructor(
        self, db: Session, *, obj_in: GroupCreate, instructor_id: Optional[int] = None
    ) -> Group:
        obj_in_data = obj_in.dict()
        if instructor_id:
            obj_in_data["instructor_id"] = instructor_id
        db_obj = Group(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_with_details(self, db: Session, id: int) -> Optional[Group]:
        return db.query(Group).options(
            joinedload(Group.instructor),
            joinedload(Group.registrations).joinedload("visitor")
        ).filter(Group.id == id).first()
    
    def get_multi_with_details(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Group]:
        return db.query(Group).options(
            joinedload(Group.instructor),
            joinedload(Group.registrations).joinedload("visitor")
        ).offset(skip).limit(limit).all()
    
    def get_upcoming_groups(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Group]:
        now = datetime.now()
        return db.query(Group).options(
            joinedload(Group.instructor)
        ).filter(Group.start_time > now).order_by(Group.start_time).offset(skip).limit(limit).all()
    
    def get_instructor_groups(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Group]:
        return db.query(Group).filter(
            Group.instructor_id == instructor_id
        ).order_by(Group.start_time).offset(skip).limit(limit).all()
    
    def get_visitor_available_groups(
        self, db: Session, *, visitor_id: int, gender: str, skip: int = 0, limit: int = 100
    ) -> List[Group]:
        now = datetime.now()
        
        # Get all groups that the visitor is already registered for
        registered_group_ids = db.query(Group.id).join(
            "registrations"
        ).filter(Group.registrations.any(visitor_id=visitor_id)).all()
        registered_group_ids = [g[0] for g in registered_group_ids]
        
        # Get groups that still have capacity based on gender
        if gender == 'male':
            query = db.query(Group).filter(
                Group.start_time > now,
                ~Group.id.in_(registered_group_ids) if registered_group_ids else True,
                func.count(Group.registrations) < Group.capacity,
                func.sum(func.case([(User.gender == 'male', 1)], else_=0)) < Group.max_male
            )
        elif gender == 'female':
            query = db.query(Group).filter(
                Group.start_time > now,
                ~Group.id.in_(registered_group_ids) if registered_group_ids else True,
                func.count(Group.registrations) < Group.capacity,
                func.sum(func.case([(User.gender == 'female', 1)], else_=0)) < Group.max_female
            )
        else:
            # For other genders, just check total capacity
            query = db.query(Group).filter(
                Group.start_time > now,
                ~Group.id.in_(registered_group_ids) if registered_group_ids else True,
                func.count(Group.registrations) < Group.capacity
            )
        
        return query.options(
            joinedload(Group.instructor)
        ).order_by(Group.start_time).offset(skip).limit(limit).all()
    
    def update_instructor(
        self, db: Session, *, group_id: int, new_instructor_id: Optional[int]
    ) -> Group:
        group = self.get(db, id=group_id)
        if group:
            group.instructor_id = new_instructor_id
            db.add(group)
            db.commit()
            db.refresh(group)
        return group


group = CRUDGroup(Group)
