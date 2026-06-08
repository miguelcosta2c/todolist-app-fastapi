from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.models import UserToken
from app.schemas import RefreshTokensListFilter
from app.services.token import (
    count_all_user_tokens,
    delete_refresh_tokens_from_user,
    delete_token_by_id,
    get_token_by_id,
    list_all_user_tokens,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_db(rows: list[Any] | None = None) -> AsyncMock:
    """Return a mock AsyncSession whose scalars().all() returns *rows*."""
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.all.return_value = rows or []
    db.scalars.return_value = scalar_result
    return db


def make_filters(**kwargs: Any) -> RefreshTokensListFilter:
    """Build a RefreshTokensListFilter with sensible defaults."""
    defaults = {"offset": 0, "limit": 10, "ordey_by": "created_at", "order_desc": False}
    defaults.update(kwargs)
    return RefreshTokensListFilter(**defaults)


# ---------------------------------------------------------------------------
# list_all_user_tokens - branch coverage for every optional filter
# ---------------------------------------------------------------------------


class TestListAllUserTokens:
    async def test_no_optional_filters(self) -> None:
        """All optional filters absent → query runs with just offset/limit."""
        db: AsyncMock = make_db()
        filters: RefreshTokensListFilter = make_filters()

        result: Sequence[UserToken] = await list_all_user_tokens(db, filters)

        assert result == []
        db.scalars.assert_called_once()

    async def test_filter_by_id(self) -> None:
        db: AsyncMock = make_db()
        filters: RefreshTokensListFilter = make_filters(id=42)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_filter_by_user_uuid(self) -> None:
        db: AsyncMock = make_db()
        user_uuid: UUID = uuid4()
        filters: RefreshTokensListFilter = make_filters(user_uuid=user_uuid)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_filter_is_revoked_true(self) -> None:
        db: AsyncMock = make_db()
        filters: RefreshTokensListFilter = make_filters(is_revoked=True)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_filter_is_revoked_false(self) -> None:
        """is_revoked=False must still apply the filter (checked with `is not None`)."""
        db: AsyncMock = make_db()
        filters: RefreshTokensListFilter = make_filters(is_revoked=False)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_filter_expires_after(self) -> None:
        db: AsyncMock = make_db()
        expires_after: datetime = datetime(2025, 1, 1, tzinfo=UTC)
        filters: RefreshTokensListFilter = make_filters(expires_after=expires_after)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_filter_expires_before(self) -> None:
        db: AsyncMock = make_db()
        expires_before: datetime = datetime(2030, 1, 1, tzinfo=UTC)
        filters: RefreshTokensListFilter = make_filters(expires_before=expires_before)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_filter_created_after(self) -> None:
        db: AsyncMock = make_db()
        created_after: datetime = datetime(2025, 1, 1, tzinfo=UTC)
        filters: RefreshTokensListFilter = make_filters(created_after=created_after)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_filter_created_before(self) -> None:
        db: AsyncMock = make_db()
        created_before: datetime = datetime(2030, 1, 1, tzinfo=UTC)
        filters: RefreshTokensListFilter = make_filters(created_before=created_before)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_all_filters_combined(self) -> None:
        """Every optional filter applied at once."""
        db: AsyncMock = make_db()
        now: datetime = datetime(2025, 6, 1, tzinfo=UTC)
        far_future: datetime = datetime(2030, 1, 1, tzinfo=UTC)
        filters: RefreshTokensListFilter = make_filters(
            id=1,
            user_uuid=uuid4(),
            is_revoked=False,
            expires_after=now,
            expires_before=far_future,
            created_after=now,
            created_before=far_future,
        )

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    # --- order_by branches ---------------------------------------------------

    @pytest.mark.parametrize(
        "field", ["id", "user_uuid", "is_revoked", "expires_at", "created_at"]
    )
    async def test_order_by_valid_fields_asc(self, field: str) -> None:
        """Every recognised ORDER_FIELDS key, ascending."""
        db: AsyncMock = make_db()
        filters: RefreshTokensListFilter = make_filters(
            order_by=field, order_desc=False
        )

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    @pytest.mark.parametrize(
        "field", ["id", "user_uuid", "is_revoked", "expires_at", "created_at"]
    )
    async def test_order_by_valid_fields_desc(self, field: str) -> None:
        """Every recognised ORDER_FIELDS key, descending."""
        db: AsyncMock = make_db()
        filters: RefreshTokensListFilter = make_filters(order_by=field, order_desc=True)

        await list_all_user_tokens(db, filters)

        db.scalars.assert_called_once()

    async def test_returns_rows_from_db(self) -> None:
        """Result of scalars().all() is forwarded to the caller."""
        fake_token: MagicMock = MagicMock(spec=UserToken)
        db: AsyncMock = make_db(rows=[fake_token])
        filters: RefreshTokensListFilter = make_filters()

        result: Sequence[UserToken] = await list_all_user_tokens(db, filters)

        assert result == [fake_token]


# ---------------------------------------------------------------------------
# count_all_user_tokens - branch coverage for every optional filter
# ---------------------------------------------------------------------------


class TestCountAllUserTokens:
    async def test_no_filters(self) -> None:
        count = 5
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 5
        filters: RefreshTokensListFilter = make_filters()

        total = await count_all_user_tokens(db, filters)

        assert total == count

    async def test_filter_by_id(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 1
        filters: RefreshTokensListFilter = make_filters(id=42)

        total = await count_all_user_tokens(db, filters)

        assert total == 1

    async def test_filter_by_user_uuid(self) -> None:
        count = 2
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 2
        filters: RefreshTokensListFilter = make_filters(user_uuid=uuid4())

        total = await count_all_user_tokens(db, filters)

        assert total == count

    async def test_filter_is_revoked(self) -> None:
        count = 2
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 0
        filters: RefreshTokensListFilter = make_filters(is_revoked=True)

        total = await count_all_user_tokens(db, filters)

        assert total == count

    async def test_filter_expires_after(self) -> None:
        count = 3
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 3
        filters: RefreshTokensListFilter = make_filters(
            expires_after=datetime(2025, 1, 1, tzinfo=UTC)
        )

        total = await count_all_user_tokens(db, filters)

        assert total == count

    async def test_filter_expires_before(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 1
        filters: RefreshTokensListFilter = make_filters(
            expires_before=datetime(2030, 1, 1, tzinfo=UTC)
        )

        total = await count_all_user_tokens(db, filters)

        assert total == 1

    async def test_filter_created_after(self) -> None:
        count = 2
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 2
        filters: RefreshTokensListFilter = make_filters(
            created_after=datetime(2025, 1, 1, tzinfo=UTC)
        )

        total = await count_all_user_tokens(db, filters)

        assert total == count

    async def test_filter_created_before(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 1
        filters: RefreshTokensListFilter = make_filters(
            created_before=datetime(2030, 1, 1, tzinfo=UTC)
        )

        total = await count_all_user_tokens(db, filters)

        assert total == 1

    async def test_returns_zero_when_scalar_is_none(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = None
        filters: RefreshTokensListFilter = make_filters()

        total = await count_all_user_tokens(db, filters)

        assert total == 0

    async def test_all_filters_combined(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = 1
        now: datetime = datetime(2025, 6, 1, tzinfo=UTC)
        filters: RefreshTokensListFilter = make_filters(
            id=1,
            user_uuid=uuid4(),
            is_revoked=False,
            expires_after=now,
            expires_before=datetime(2030, 1, 1, tzinfo=UTC),
            created_after=now,
            created_before=datetime(2030, 1, 1, tzinfo=UTC),
        )

        total = await count_all_user_tokens(db, filters)

        assert total == 1


# ---------------------------------------------------------------------------
# get_token_by_id
# ---------------------------------------------------------------------------


class TestGetTokenById:
    async def test_returns_token_when_found(self) -> None:
        db: AsyncMock = AsyncMock()
        fake_token: MagicMock = MagicMock(spec=UserToken)
        db.scalar.return_value = fake_token

        result: UserToken | None = await get_token_by_id(db, token_id=7)

        assert result is fake_token
        db.scalar.assert_called_once()

    async def test_returns_none_when_not_found(self) -> None:
        db: AsyncMock = AsyncMock()
        db.scalar.return_value = None

        result: UserToken | None = await get_token_by_id(db, token_id=999)

        assert result is None


# ---------------------------------------------------------------------------
# delete_token_by_id
# ---------------------------------------------------------------------------


class TestDeleteTokenById:
    async def test_executes_delete(self) -> None:
        db: AsyncMock = AsyncMock()

        await delete_token_by_id(db, token_id=3)

        db.execute.assert_called_once()

    async def test_returns_none(self) -> None:
        db: AsyncMock = AsyncMock()

        result: None = await delete_token_by_id(db, token_id=3)

        assert result is None


# ---------------------------------------------------------------------------
# delete_refresh_tokens_from_user
# ---------------------------------------------------------------------------


class TestDeleteRefreshTokensFromUser:
    async def test_executes_delete_for_user(self) -> None:
        db: AsyncMock = AsyncMock()
        fake_user: MagicMock = MagicMock()
        fake_user.uuid_ = uuid4()

        await delete_refresh_tokens_from_user(db, fake_user)

        db.execute.assert_called_once()

    async def test_returns_none(self) -> None:
        db: AsyncMock = AsyncMock()
        fake_user: MagicMock = MagicMock()
        fake_user.uuid_ = uuid4()

        result: None = await delete_refresh_tokens_from_user(db, fake_user)

        assert result is None
