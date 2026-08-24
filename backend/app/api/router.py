from fastapi import APIRouter

from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.projects import router as projects_router
from backend.app.api.routes.agent_outputs import (
    router as agent_outputs_router,
)
from backend.app.api.routes.teams import (
    router as teams_router,
)
from backend.app.api.routes.meetings import (
    router as meetings_router,
)

api_router = APIRouter()

api_router.include_router(
    health_router
)

api_router.include_router(
    auth_router
)

api_router.include_router(
    projects_router
)

api_router.include_router(
    agent_outputs_router
)

api_router.include_router(
    teams_router
)
api_router.include_router(
    meetings_router
)