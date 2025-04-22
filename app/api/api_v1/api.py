
from fastapi import APIRouter

from app.api.api_v1.endpoints import login, users, groups, registrations, instructors

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(registrations.router, prefix="/registrations", tags=["registrations"])
api_router.include_router(instructors.router, prefix="/instructors", tags=["instructors"])
