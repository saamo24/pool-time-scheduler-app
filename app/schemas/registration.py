
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Shared properties
class RegistrationBase(BaseModel):
    group_id: int
    attended: Optional[bool] = False

# Properties to receive via API on creation
class RegistrationCreate(RegistrationBase):
    pass

# Properties to receive via API on update
class RegistrationUpdate(BaseModel):
    attended: Optional[bool] = None

class RegistrationInDBBase(RegistrationBase):
    id: int
    visitor_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Additional properties to return via API
class Registration(RegistrationInDBBase):
    pass
