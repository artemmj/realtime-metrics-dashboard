from fastapi import APIRouter


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/")
def get_users() -> list[dict]:
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.get("/me")
def get_current_user() -> dict:
    return {"username": "Rick", "role": "admin"}
