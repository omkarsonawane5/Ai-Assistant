from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import UserSettings

class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, user_id: str) -> UserSettings:
        settings = await self.session.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
        if settings is None:
            settings = UserSettings(user_id=user_id)
            self.session.add(settings)
            await self.session.flush()
        return settings
