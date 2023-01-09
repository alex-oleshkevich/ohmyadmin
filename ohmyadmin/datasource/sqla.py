from __future__ import annotations

import sqlalchemy as sa
import typing
from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import NamedColumn
from starlette.requests import Request

from ohmyadmin.datasource.base import DataSource
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Page


def get_column_properties(entity_class: typing.Any, prop_names: typing.Sequence[str]) -> dict[str, orm.ColumnProperty]:
    """
    Return SQLAlchemy columns defined on entity class by their string names.

    Looks up in the relations too.
    """
    mapper: orm.Mapper = orm.class_mapper(entity_class)
    props: dict[str, orm.ColumnProperty] = {}
    for name in prop_names:
        if name in mapper.all_orm_descriptors:
            props[name] = mapper.all_orm_descriptors[name].property
        elif '.' in name:
            related_attr, related_column = name.split('.')
            if related_property := mapper.all_orm_descriptors.get(related_attr):
                props[name] = related_property.entity.all_orm_descriptors[related_column].property
    return props


def create_search_token(column: NamedColumn, search_query: str) -> sa.sql.ColumnElement:
    string_column = sa.cast(column, sa.Text)
    if search_query.startswith('^'):
        search_token = f'{search_query[1:].lower()}%'
        return string_column.ilike(search_token)

    if search_query.startswith('='):
        search_token = f'{search_query[1:].lower()}'
        return sa.func.lower(string_column) == search_token

    if search_query.startswith('@'):
        search_token = f'{search_query[1:].lower()}'
        return string_column.regexp_match(search_token)

    search_token = f'%{search_query.lower()}%'
    return string_column.ilike(search_token)


class SQLADataSource(DataSource):
    def __init__(
        self,
        model_class: typing.Any,
        async_session: async_sessionmaker,
        query: sa.Select | None = None,
        query_for_list: sa.Select | None = None,
        _stmt: sa.Select | None = None,
    ) -> None:
        self.model_class = model_class
        self.async_session = async_session
        self.query = query if query is not None else sa.select(model_class)
        self.query_for_list = query_for_list if query_for_list is not None else self.query
        self._stmt = _stmt if _stmt is not None else self.query

    def get_for_index(self) -> DataSource:
        return self._clone(self.query_for_list)

    def apply_search(self, search_term: str, searchable_fields: typing.Sequence[str]) -> DataSource:
        if not search_term:
            return self._clone(self._stmt)

        clauses = []
        props = get_column_properties(self.model_class, searchable_fields)
        for prop in props.values():
            if len(prop.columns) > 1:
                continue
            clauses.append(create_search_token(prop.columns[0], search_term))
        return self._clone(self._stmt.where(sa.or_(*clauses)))

    def apply_ordering(self, ordering: dict[str, SortingType], sortable_fields: typing.Sequence[str]) -> DataSource:
        stmt = self._stmt.order_by(None)
        props = get_column_properties(self.model_class, sortable_fields)

        for ordering_field, ordering_dir in ordering.items():
            try:
                prop = props[ordering_field]
                if len(prop.columns) > 1:
                    continue
                column = prop.columns[0]
                stmt = stmt.order_by(column.desc() if ordering_dir == 'desc' else column.asc())
            except KeyError:
                # ordering_field does not exist in properties, ignore
                continue
        return self._clone(stmt)

    async def count(self, session: AsyncSession) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(self._stmt)
        result = await session.scalars(stmt)
        return result.one()

    async def one(self) -> typing.Any:
        pass

    async def paginate(self, request: Request, page: int, page_size: int) -> Page[typing.Any]:
        async with self.async_session() as session:
            row_count = await self.count(session)

            offset = (page - 1) * page_size
            stmt = self._stmt.limit(page_size).offset(offset)
            result = await session.scalars(stmt)
            rows = result.all()
            return Page(rows=list(rows), total_rows=row_count, page=page, page_size=page_size)

    def _clone(self, stmt: sa.Select) -> SQLADataSource:
        return self.__class__(
            model_class=self.model_class,
            async_session=self.async_session,
            query=self.query,
            query_for_list=self.query_for_list,
            _stmt=stmt,
        )
