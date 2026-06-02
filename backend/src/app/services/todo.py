import uuid
from collections.abc import Sequence
from typing import Literal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Todo
from app.schemas import TodoCreate, TodoListFilters


ORDER_FIELDS: dict[str, Literal[
    "created_at",
    "updated_at",
    "due_date",
    "priority",
    "status",
]] = {
    "created_at": Todo.created_at,
    "updated_at": Todo.updated_at,
    "due_date": Todo.due_date,
    "priority": Todo.priority,
    "status": Todo.status,
}


class TodoDBService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_todos_by_user(
        self, user_uuid: uuid.UUID, filters: TodoListFilters
    ) -> Sequence[Todo]:
        stmt = select(Todo).where(Todo.user_uuid == user_uuid)

        if filters.status:
            stmt = stmt.where(Todo.status == filters.status)

        if filters.priority:
            stmt = stmt.where(Todo.priority == filters.priority)

        if filters.created_after:
            stmt = stmt.where(Todo.created_at >= filters.created_after)

        if filters.created_before:
            stmt = stmt.where(Todo.created_at <= filters.created_before)

        column = ORDER_FIELDS.get(filters.order_by, Todo.created_at)

        stmt = (
            stmt.order_by(desc(column) if filters.order_desc else column)
            .offset(filters.offset)
            .limit(filters.limit)
        )

        result = await self.session.scalars(stmt)
        return result.all()

    async def get_todo_by_uuid(
        self, todo_uuid: uuid.UUID, user_uuid: uuid.UUID
    ) -> Todo | None:
        return await self.session.scalar(
            select(Todo).where(
                Todo.uuid_ == todo_uuid,
                Todo.user_uuid == user_uuid,
            )
        )

    async def get_all_todos(
        self, filters: TodoListFilters
    ) -> Sequence[Todo]:
        stmt = select(Todo)

        if filters.status:
            stmt = stmt.where(Todo.status == filters.status)

        if filters.priority:
            stmt = stmt.where(Todo.priority == filters.priority)

        if filters.created_after:
            stmt = stmt.where(Todo.created_at >= filters.created_after)

        if filters.created_before:
            stmt = stmt.where(Todo.created_at <= filters.created_before)

        column = ORDER_FIELDS.get(filters.order_by, Todo.created_at)

        stmt = (
            stmt.order_by(desc(column) if filters.order_desc else column)
            .offset(filters.offset)
            .limit(filters.limit)
        )

        result = await self.session.scalars(stmt)
        return result.all()

    async def get_todo_by_uuid_admin(
        self, todo_uuid: uuid.UUID
    ) -> Todo | None:
        return await self.session.scalar(
            select(Todo).where(Todo.uuid_ == todo_uuid)
        )

    async def create_todo(
        self, data: TodoCreate, user_uuid: uuid.UUID
    ) -> Todo:
        todo = Todo(
            name=data.name,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            user_uuid=user_uuid,
        )

        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)

        return todo

    async def update_todo(
        self, todo: Todo, data: dict
    ) -> Todo:
        updated = False
        for field, value in data.items():
            if getattr(todo, field) != value:
                updated = True
                setattr(todo, field, value)

        if updated:
            await self.session.commit()
            await self.session.refresh(todo)

        return todo

    async def delete_todo(self, todo: Todo) -> None:
        await self.session.delete(todo)
        await self.session.commit()
