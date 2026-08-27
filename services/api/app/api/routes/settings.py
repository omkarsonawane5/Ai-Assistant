from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.repositories.settings import SettingsRepository
from app.db.session import get_db_session
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("", response_model=SettingsResponse)
async def get_settings(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    return await SettingsRepository(session).get_for_user(user.id)

@router.put("", response_model=SettingsResponse)
async def update_settings(payload: SettingsUpdate, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    settings = await SettingsRepository(session).get_for_user(user.id)
    settings.preferred_model = payload.preferred_model
    settings.response_style = payload.response_style
    await session.commit()
    return settings
