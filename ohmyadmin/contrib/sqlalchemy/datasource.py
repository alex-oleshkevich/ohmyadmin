from __future__ import annotations

import datetime
import decimal
import sqlalchemy as sa
import typing
import uuid
from sqlalchemy import orm
from sqlalchemy.sql.elements import NamedColumn
from starlette.requests import Request

from ohmyadmin.datasource.base import DataSource, NumberOperation, StringOperation
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination


def get_column_properties(model_class: typing.Any, prop_names: typing.Sequence[str]) -> dict[str, orm.ColumnProperty]:
    """
    Return SQLAlchemy columns defined on entity class by their string names.

    Looks up in the relations too.
    """
    mapper: orm.Mapper = orm.class_mapper(model_class)
    props: dict[str, orm.ColumnProperty] = {}
    for name in prop_names:
        if name in mapper.all_orm_descriptors:
            props[name] = mapper.all_orm_descriptors[name].property  # type: ignore[attr-defined]
        elif '.' in name:
            related_attr, related_column = name.split('.')
            if related_property := mapper.all_orm_descriptors.get(related_attr):
                props[name] = related_property.entity.all_orm_descriptors[  # type: ignore[attr-defined]
                    related_column
                ].property  # type: ignore[attr-defined]
    return props


def create_search_token(column: NamedColumn, search_query: str) -> sa.sql.ColumnElement:
    string_column = sa.cast(column, sa.Text)
    if search_query.startswith('^'):
        search_token = f'{search_query[1:].lower()}%'
        return string_column.startswith(search_token)

    if search_query.startswith('='):
        search_token = f'{search_query[1:].lower()}'
        return string_column == search_token

    if search_query.startswith('@'):
        search_token = f'{search_query[1:].lower()}'
        return string_column.regexp_match(search_token)

    if search_query.startswith('$'):
        search_token = f'{search_query[1:].lower()}'
        return string_column.endswith(search_token)

    search_token = f'%{search_query.lower()}%'
    return string_column.ilike(search_token)


def guess_pk_field(model_class: type) -> str:
    mapper: orm.Mapper = orm.class_mapper(model_class)
    pk_columns = [
        c.name for c in mapper.all_orm_descriptors if hasattr(c, 'primary_key') and c.primary_key  # type: ignore
    ]
    assert len(pk_columns), f'Model class {model_class} does not contain any primary key.'
    assert len(pk_columns) == 1, f'Model class {model_class} defines composite primary key which are not supported.'
    return pk_columns[0]


def guess_pk_type(model_class: type, pk_field: str) -> typing.Callable:
    mapper: orm.Mapper = orm.class_mapper(model_class)
    column = mapper.columns[pk_field]
    match column.type:
        case sa.String() | sa.Text():
            return str
        case sa.Integer():
            return int
        case sa.Float():
            return float
        case sa.Numeric():
            return decimal.Decimal
        case sa.Uuid():
            return uuid.UUID
    raise ValueError(f'Failed to guess primary key column caster for {column} (type={column.type}).')


T = typing.TypeVar('T', bound=typing.Any)


class SQLADataSource(DataSource[T]):
    def __init__(
        self,
        model_class: type[T],
        query: sa.Select | None = None,
        query_for_list: sa.Select | None = None,
        pk_column: str | None = None,
        pk_cast: typing.Callable | None = None,
        _stmt: sa.Select | None = None,
    ) -> None:
        self.pk_column = pk_column or guess_pk_field(model_class)
        self.pk_cast = pk_cast or guess_pk_type(model_class, self.pk_column)
        self.model_class = model_class
        self.query = query if query is not None else sa.select(model_class)
        self.query_for_list = query_for_list if query_for_list is not None else self.query
        self._stmt = _stmt if _stmt is not None else self.query

    @property
    def raw(self) -> sa.Select[T]:
        return self._stmt

    def get_query(self) -> SQLADataSource[T]:
        return self._clone(self.query)

    def get_query_for_index(self) -> SQLADataSource[T]:
        return self._clone(self.query_for_list)

    def get_pk(self, obj: T) -> str:
        return str(getattr(obj, self.pk_column))

    def new(self) -> T:
        return self.model_class()

    def apply_search(self, search_term: str, searchable_fields: typing.Sequence[str]) -> SQLADataSource[T]:
        if not search_term:
            return self._clone(self._stmt)

        clauses = []
        props = get_column_properties(self.model_class, searchable_fields)
        for prop in props.values():
            if len(prop.columns) > 1:  # pragma: no cover, no idea
                continue
            clauses.append(create_search_token(prop.columns[0], search_term))
        return self._clone(self._stmt.where(sa.or_(*clauses)))

    def apply_ordering(
        self,
        ordering: dict[str, SortingType],
        sortable_fields: typing.Sequence[str],
    ) -> SQLADataSource[T]:
        stmt = self._stmt.order_by(None)
        props = get_column_properties(self.model_class, sortable_fields)

        for ordering_field, ordering_dir in ordering.items():
            try:
                prop = props[ordering_field]
                if len(prop.columns) > 1:  # pragma: no cover
                    continue
                column = prop.columns[0]
                stmt = stmt.order_by(column.desc() if ordering_dir == 'desc' else column.asc())
            except KeyError:
                # ordering_field does not exist in properties, ignore
                continue
        return self._clone(stmt)

    def apply_string_filter(self, field: str, operation: StringOperation, value: str) -> SQLADataSource[T]:
        column = getattr(self.model_class, field)
        expr: sa.sql.ColumnElement = sa.func.lower(column)

        mapping = {
            StringOperation.exact: lambda stmt: stmt.where(expr == value),
            StringOperation.startswith: lambda stmt: stmt.where(expr.startswith(value)),
            StringOperation.endswith: lambda stmt: stmt.where(expr.endswith(value)),
            StringOperation.contains: lambda stmt: stmt.where(expr.like(f'%{value}%')),
            StringOperation.pattern: lambda stmt: stmt.where(expr.regexp_match(value)),
        }
        filter_ = mapping[operation]
        return self._clone(filter_(self._stmt))

    def apply_number_filter(
        self, field: str, operation: NumberOperation, value: int | float | decimal.Decimal
    ) -> SQLADataSource[T]:
        column = getattr(self.model_class, field)
        number_column = sa.sql.cast(column, sa.Integer)
        mapping = {
            NumberOperation.eq: lambda stmt: stmt.where(number_column == value),
            NumberOperation.gt: lambda stmt: stmt.where(number_column > value),
            NumberOperation.gte: lambda stmt: stmt.where(number_column >= value),
            NumberOperation.lt: lambda stmt: stmt.where(number_column < value),
            NumberOperation.lte: lambda stmt: stmt.where(number_column <= value),
        }
        filter_ = mapping[operation]
        return self._clone(filter_(self._stmt))

    def apply_date_filter(self, field: str, value: datetime.date) -> SQLADataSource[T]:
        column = getattr(self.model_class, field)
        return self._clone(self._stmt.where(column == value))

    def apply_date_range_filter(
        self, field: str, before: datetime.date | None, after: datetime.date | None
    ) -> SQLADataSource[T]:
        column = getattr(self.model_class, field)
        query = self
        if before:
            query = query._clone(query._stmt.where(column <= before))
        if after:
            query = query._clone(query._stmt.where(column >= after))
        return query

    def apply_choice_filter(self, field: str, choices: list[typing.Any], coerce: typing.Callable) -> SQLADataSource[T]:
        column = getattr(self.model_class, field)
        return self._clone(self._stmt.where(column.in_(choices)))

    def apply_boolean_filter(self, field: str, value: bool) -> SQLADataSource[T]:
        column = getattr(self.model_class, field)
        return self._clone(self._stmt.where(column.is_(value)))

    async def count(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(self._stmt)  # type: ignore[arg-type]
        result = await request.state.dbsession.scalars(stmt)
        return result.one()

    async def get(self, request: Request, pk: str) -> typing.Any:
        column = getattr(self.model_class, self.pk_column)
        stmt = self.get_query()._stmt.where(column == self.pk_cast(pk))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()

    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[typing.Any]:
        row_count = await self.count(request)

        offset = (page - 1) * page_size
        stmt = self._stmt.limit(page_size).offset(offset)
        result = await request.state.dbsession.scalars(stmt)
        rows = result.all()
        return Pagination(rows=list(rows), total_rows=row_count, page=page, page_size=page_size)

    async def create(self, request: Request, model: typing.Any) -> None:
        request.state.dbsession.add(model)
        await request.state.dbsession.commit()

    async def update(self, request: Request, model: typing.Any) -> None:
        await request.state.dbsession.commit()

    async def delete(self, request: Request, *object_ids: str) -> None:
        typed_ids = list(map(self.pk_cast, object_ids))
        stmt = sa.delete(self.model_class).where(sa.column(self.pk_column).in_(typed_ids))
        async for instance in await request.state.dbsession.stream(stmt):
            await request.state.dbsession.delete(instance)
        await request.state.dbsession.commit()

    def _clone(self, stmt: sa.Select | None = None) -> SQLADataSource:
        return self.__class__(
            query=self.query,
            model_class=self.model_class,
            query_for_list=self.query_for_list,
            _stmt=stmt if stmt is not None else self._stmt,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return repr(self._stmt)
