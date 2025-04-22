
# Import all the models so that Alembic can discover them
from app.db.base_class import Base
from app.models.user import User
from app.models.group import Group
from app.models.registration import Registration
from app.models.instructor_schedule import InstructorSchedule
from app.models.instructor_preference import InstructorPreference
