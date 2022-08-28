from __future__ import annotations

import sqlalchemy as sa
import typing
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

from ohmyadmin.collection import Collection
from ohmyadmin.pagination import Page

E = typing.TypeVar('E', bound=DeclarativeMeta)


class Query:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def one(self, selectable: sa.sql.Select) -> typing.Any:
        result = await self.session.scalars(selectable)
        return result.one()

    async def one_or_none(self, selectable: sa.sql.Select) -> typing.Any | None:
        result = await self.session.scalars(selectable)
        return result.one_or_none()

    async def get(self, entity_class: typing.Type[E], pk: typing.Any, pk_column: str = 'id') -> E:
        stmt = sa.select(entity_class).where().where(getattr(entity_class, pk_column) == pk).limit(1)
        return await self.one(stmt)

    async def find(self, entity_class: typing.Type[E], pk: typing.Any, pk_column: str = 'id') -> E | None:
        stmt = sa.select(entity_class).where().where(getattr(entity_class, pk_column) == pk).limit(1)
        return await self.one_or_none(stmt)

    async def find_all(self, entity_class: typing.Type[E]) -> Collection[E]:
        stmt = sa.select(entity_class)
        return await self.all(stmt)

    async def first(self, selectable: sa.sql.Select) -> typing.Any | None:
        result = await self.session.scalars(selectable.limit(1))
        return result.first()

    async def all(self, selectable: sa.sql.Select) -> Collection[typing.Any]:
        result = await self.session.scalars(selectable)
        return Collection(result.all())

    async def choices(
        self, selectable: sa.sql.Select, label_column: str = 'name', value_column: str = 'id'
    ) -> list[tuple[str, typing.Any]]:
        result = await self.session.scalars(selectable)
        return Collection(result.all()).choices(label_col=label_column, value_col=value_column)

    async def choices_dict(
        self,
        selectable: sa.sql.Select,
        label_column: str = 'name',
        value_column: str = 'id',
        label_key: str = 'label',
        value_key: str = 'value',
    ) -> list[dict[typing.Any, typing.Any]]:
        result = await self.session.scalars(selectable)
        return Collection(result.all()).choices_dict(
            label_col=label_column,
            value_col=value_column,
            label_key=label_key,
            value_key=value_key,
        )

    async def exists(self, selectable: sa.sql.Select) -> bool:
        stmt = sa.select(sa.exists(selectable))
        result = await self.session.scalars(stmt)
        return result.one() is True

    async def count(self, selectable: sa.sql.Select) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(selectable)
        result = await self.session.scalars(stmt)
        return result.one()

    async def paginate(self, selectable: sa.sql.Select, page: int = 1, page_size: int = 50) -> Page:
        offset = (page - 1) * page_size
        total = await self.count(selectable)
        rows = await self.all(selectable.limit(page_size).offset(offset))
        return Page(list(rows), total, page, page_size)

    async def execute(self, selectable: sa.sql.Select) -> typing.Any:
        return await self.session.execute(selectable)


query = Query
