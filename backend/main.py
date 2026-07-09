from fastapi import FastAPI
from src.routes.users import router as users_router

app = FastAPI(title="Realtime Metrics Dashboard. Backend")

app.include_router(users_router)


@app.get("/")
def root():
    return "It's worked!"
