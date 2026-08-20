from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.admin_router import router as admin_router
from app.routers.jobs_router import router as jobs_router
from app.routers.skill_router import router as skill_router
from app.routers.user_skill_router  import router as user_skill_router
from app.routers.job_skill_router import router as job_skill_router
from app.routers.proposals_router import router as proposals_router
from app.routers.messages_router import router as messages_router
from app.routers.notifications_router import router as notifications_router
app = FastAPI()



app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(jobs_router)
app.include_router(skill_router)
app.include_router(user_skill_router)
app.include_router(job_skill_router)
app.include_router(proposals_router)
app.include_router(messages_router)
app.include_router(notifications_router)