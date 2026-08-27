from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.db.models import User
from app.schemas.auth import UserResponse

router = APIRouter(tags=["users"])

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)
