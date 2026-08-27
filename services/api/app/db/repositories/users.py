from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, UserSettings
from app.security.auth import hash_password

class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email.lower()))

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.session.get(User, user_id)

    async def create(self, email: str, password: str, display_name: str | None = None) -> User:
        user = User(email=email.lower(), password_hash=hash_password(password), display_name=display_name)
        self.session.add(user)
        await self.session.flush()
        self.session.add(UserSettings(user_id=user.id))
        await self.session.flush()
        return user
