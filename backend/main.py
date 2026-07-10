from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from src.routes.auth import router as auth_router
from src.routes.users import router as users_router

app = FastAPI(
    title="Realtime Metrics Dashboard. Backend",
    root_path="/api",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app_router = APIRouter()

app_router.include_router(auth_router, prefix="/v1")
app_router.include_router(users_router, prefix="/v1")

app.include_router(app_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
