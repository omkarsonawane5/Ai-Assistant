import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.api.dependencies import get_current_user
from app.db.models import Base, User
from app.db.session import get_db_session
from app.main import app
from app.security.auth import hash_password

@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as session:
        user = User(email="test@example.com", password_hash=hash_password("password"), display_name="Test")
        other = User(email="other@example.com", password_hash=hash_password("password"), display_name="Other")
        session.add_all([user, other])
        await session.commit()
        user_id = user.id
        other_id = other.id
    async def override_db():
        async with Session() as session:
            yield session
    async def override_user():
        async with Session() as session:
            return await session.get(User, user_id)
    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = override_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ac.test_user_id = user_id
        ac.other_user_id = other_id
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.asyncio
async def test_conversation_vertical_slice(client):
    created = await client.post("/conversations", json={"title": "Test chat"})
    assert created.status_code == 201
    conv_id = created.json()["id"]
    stream = await client.post(f"/conversations/{conv_id}/messages/stream", json={"content": "Hello"})
    assert stream.status_code == 200
    assert "text.delta" in stream.text
    messages = await client.get(f"/conversations/{conv_id}/messages")
    assert messages.status_code == 200
    payload = messages.json()
    assert [m["role"] for m in payload] == ["user", "assistant"]
    assert "Hello" in payload[1]["content"]

@pytest.mark.asyncio
async def test_unauthorized_conversation_access_is_not_found(client):
    from app.db.repositories.conversations import ConversationRepository
    from app.db.session import get_db_session as dep
    override = app.dependency_overrides[dep]
    async for session in override():
        other_conv = await ConversationRepository(session).create(client.other_user_id, "Private")
        await session.commit()
        other_id = other_conv.id
        break
    response = await client.get(f"/conversations/{other_id}")
    assert response.status_code == 404
