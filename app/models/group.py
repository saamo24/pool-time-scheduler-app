
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base, BaseModel
from datetime import datetime, timedelta

class Group(Base, BaseModel):
    __tablename__ = "groups"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=False)
    max_male = Column(Integer, nullable=False)
    max_female = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Foreign keys
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    instructor = relationship("User", back_populates="groups")
    registrations = relationship("Registration", back_populates="group", cascade="all, delete-orphan")
    
    @property
    def duration_hours(self):
        """Get the duration of the group session in hours"""
        if not self.start_time or not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600
    
    @property
    def current_participants(self):
        """Get the current number of participants"""
        return len(self.registrations)
    
    @property
    def current_male_participants(self):
        """Get the current number of male participants"""
        return sum(1 for reg in self.registrations if reg.visitor.gender == "male")
    
    @property
    def current_female_participants(self):
        """Get the current number of female participants"""
        return sum(1 for reg in self.registrations if reg.visitor.gender == "female")
    
    @property
    def is_full(self):
        """Check if the group is at full capacity"""
        return self.current_participants >= self.capacity
    
    @property
    def is_male_full(self):
        """Check if the male capacity is reached"""
        return self.current_male_participants >= self.max_male
    
    @property
    def is_female_full(self):
        """Check if the female capacity is reached"""
        return self.current_female_participants >= self.max_female
