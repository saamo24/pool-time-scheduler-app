
#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timedelta, time
import random
from pathlib import Path

# Add parent directory to path to allow module imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.base import Base
from app.db.session import engine
from app.core.security import get_password_hash
from app.models.user import User, UserRole, Gender
from app.models.group import Group
from app.models.instructor_preference import InstructorPreference, DayOfWeek
from app.models.registration import Registration

def seed_data():
    """Seed the database with initial data for testing"""
    db = SessionLocal()
    try:
        # Create admin user
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            gender=Gender.MALE
        )
        db.add(admin)
        
        # Create instructors
        instructors = []
        for i in range(1, 6):
            instructor = User(
                email=f"instructor{i}@example.com",
                hashed_password=get_password_hash(f"instructor{i}"),
                full_name=f"Instructor {i}",
                role=UserRole.INSTRUCTOR,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE
            )
            db.add(instructor)
            instructors.append(instructor)
        
        # Create visitors
        visitors = []
        for i in range(1, 21):
            visitor = User(
                email=f"visitor{i}@example.com",
                hashed_password=get_password_hash(f"visitor{i}"),
                full_name=f"Visitor {i}",
                role=UserRole.VISITOR,
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE
            )
            db.add(visitor)
            visitors.append(visitor)
        
        # Commit users first to get IDs
        db.commit()
        
        # Add instructor preferences (preferred working hours)
        days_of_week = list(DayOfWeek)
        for instructor in instructors:
            # Each instructor prefers 2-3 days
            preferred_days = random.sample(days_of_week, random.randint(2, 3))
            for day in preferred_days:
                # Morning or evening preference
                if random.choice([True, False]):
                    # Morning
                    start = time(8, 0)
                    end = time(12, 0)
                else:
                    # Evening
                    start = time(16, 0)
                    end = time(20, 0)
                
                preference = InstructorPreference(
                    instructor_id=instructor.id,
                    day_of_week=day,
                    start_time=start,
                    end_time=end
                )
                db.add(preference)
        
        # Create groups
        groups = []
        start_date = datetime.now()
        for i in range(1, 16):
            # Randomize start date within next 30 days
            days_offset = random.randint(0, 30)
            group_date = start_date + timedelta(days=days_offset)
            
            # Group time slots (1-2 hours)
            duration_hours = random.choice([1, 2])
            
            # Different time slots throughout the day
            hour_options = [8, 10, 12, 14, 16, 18]
            start_hour = random.choice(hour_options)
            
            group_start = group_date.replace(
                hour=start_hour, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            group_end = group_start + timedelta(hours=duration_hours)
            
            # Randomly assign an instructor or leave empty
            instructor_id = random.choice([None] + [i.id for i in instructors])
            
            # Random capacity limits
            total_capacity = random.randint(10, 20)
            max_male = random.randint(5, total_capacity // 2)
            max_female = total_capacity - max_male
            
            group = Group(
                name=f"Swimming Group {i}",
                description=f"Swimming session {i} for {duration_hours} hour(s)",
                capacity=total_capacity,
                max_male=max_male,
                max_female=max_female,
                start_time=group_start,
                end_time=group_end,
                instructor_id=instructor_id
            )
            db.add(group)
            groups.append(group)
        
        # Commit groups to get IDs
        db.commit()
        
        # Create some registrations for visitors
        for visitor in visitors:
            # Each visitor registers for 1-3 random groups
            num_registrations = random.randint(1, 3)
            available_groups = random.sample(groups, min(num_registrations, len(groups)))
            
            for group in available_groups:
                # Check gender-specific capacity (just a simple check for demonstration)
                gender_count = db.query(Registration).join(User).filter(
                    Registration.group_id == group.id,
                    User.gender == visitor.gender
                ).count()
                
                if visitor.gender == Gender.MALE and gender_count < group.max_male:
                    registration = Registration(
                        visitor_id=visitor.id,
                        group_id=group.id,
                        attended=random.choice([True, False])
                    )
                    db.add(registration)
                elif visitor.gender == Gender.FEMALE and gender_count < group.max_female:
                    registration = Registration(
                        visitor_id=visitor.id,
                        group_id=group.id,
                        attended=random.choice([True, False])
                    )
                    db.add(registration)
        
        db.commit()
        print("Database seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Create all tables first
    Base.metadata.create_all(bind=engine)
    
    # Seed data
    seed_data()
