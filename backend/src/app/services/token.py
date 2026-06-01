from collections.abc import Sequence

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserToken
from app.schemas import RefreshTokensListFilter

ORDER_FIELDS = {
    "id": UserToken.id,
    "user_uuid": UserToken.user_uuid,
    "is_revoked": UserToken.is_revoked,
    "expires_at": UserToken.expires_at,
    "created_at": UserToken.created_at,
}


async def list_all_user_tokens(
    db: AsyncSession, filters: RefreshTokensListFilter
) -> Sequence[UserToken]:

    stmt = select(UserToken)

    if filters.id:
        stmt = stmt.where(UserToken.id == filters.id)

    if filters.user_uuid:
        stmt = stmt.where(UserToken.user_uuid == filters.user_uuid)

    if filters.is_revoked is not None:
        stmt = stmt.where(UserToken.is_revoked == filters.is_revoked)

    if filters.expires_after:
        stmt = stmt.where(UserToken.expires_at > filters.expires_after)

    if filters.expires_before:
        stmt = stmt.where(UserToken.expires_at < filters.expires_before)

    if filters.created_after:
        stmt = stmt.where(UserToken.created_at > filters.created_after)

    if filters.created_before:
        stmt = stmt.where(UserToken.created_at < filters.created_before)

    column = ORDER_FIELDS.get(filters.order_by, User.created_at)

    stmt = (
        stmt.order_by(desc(column) if filters.order_desc else column)
        .offset(filters.offset)
        .limit(filters.limit)
    )

    result = await db.scalars(stmt)
    return result.all()


async def get_token_by_id(db: AsyncSession, token_id: int) -> UserToken | None:
    return await db.scalar(select(UserToken).where(UserToken.id == token_id))


async def delete_token_by_id(db: AsyncSession, token_id: int) -> None:
    await db.execute(delete(UserToken).where(UserToken.id == token_id))


async def delete_refresh_tokens_from_user(db: AsyncSession, user: User) -> None:
    await db.execute(delete(UserToken).where(UserToken.user_uuid == user.uuid_))
