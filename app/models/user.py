
from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base, BaseModel
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    VISITOR = "visitor"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class User(Base, BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.VISITOR, nullable=False)
    gender = Column(Enum(Gender), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    instructor_preferences = relationship("InstructorPreference", back_populates="instructor", cascade="all, delete-orphan")
    instructor_schedules = relationship("InstructorSchedule", back_populates="instructor", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="instructor")
    registrations = relationship("Registration", back_populates="visitor", cascade="all, delete-orphan")
