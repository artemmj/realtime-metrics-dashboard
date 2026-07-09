from fastapi import FastAPI, APIRouter

from src.routes.auth import router as auth_router
from src.routes.users import router as users_router

app = FastAPI(title="Realtime Metrics Dashboard. Backend")
app_router = APIRouter(prefix="/api/v1")

app_router.include_router(auth_router)
app_router.include_router(users_router)

app.include_router(app_router)


@app.get("/")
def root():
    return "I'm alive!"
