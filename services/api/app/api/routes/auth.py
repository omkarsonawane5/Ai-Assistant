from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.config.settings import Settings, get_settings
from app.db.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.security.auth import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)) -> TokenResponse:
    repo = UserRepository(session)
    user = await repo.get_by_email(str(payload.email))
    if (
        user is None
        and settings.app_env == "local"
        and str(payload.email).lower() == settings.dev_bootstrap_user_email.lower()
        and payload.password == settings.dev_bootstrap_user_password
    ):
        user = await repo.create(str(payload.email), payload.password, "Local Developer")
        await session.commit()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id, settings))

@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.status_code = status.HTTP_200_OK
    return {"status": "ok"}
