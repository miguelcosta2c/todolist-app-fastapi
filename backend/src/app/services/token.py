from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserToken


async def delete_refresh_tokens_from_user(db: AsyncSession, user: User) -> None:
    await db.execute(delete(UserToken).where(UserToken.user_uuid == user.uuid_))
