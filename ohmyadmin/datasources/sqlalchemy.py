import decimal
import functools
import typing
import uuid

import sqlalchemy as sa
import wtforms
from sqlalchemy import orm
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from ohmyadmin.datasources.datasource import (
    AndFilter,
    DataSource,
    DateFilter,
    DateOperation,
    DateTimeFilter,
    DuplicateError,
    InFilter,
    NoObjectError,
    NumberFilter,
    NumberOperation,
    OrFilter,
    QueryFilter,
    StringFilter,
    StringOperation,
    ValueFilter,
)
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination

T = typing.TypeVar(
    "T",
)


def get_dbsession(request: Request) -> AsyncSession:
    return request.state.dbsession


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
        elif "." in name:
            related_attr, related_column = name.split(".")
            if related_property := mapper.all_orm_descriptors.get(related_attr):
                props[name] = related_property.entity.all_orm_descriptors[related_column].property  # type: ignore[attr-defined]  # type: ignore[attr-defined]
    return props


def guess_pk_field(model_class: type) -> str:
    mapper: orm.Mapper = orm.class_mapper(model_class)
    pk_columns = [
        getattr(c, "name")
        for c in mapper.all_orm_descriptors
        if hasattr(c, "primary_key") and c.primary_key  # type: ignore
    ]
    assert len(pk_columns), f"Model class {model_class} does not contain any primary key."
    assert len(pk_columns) == 1, f"Model class {model_class} defines composite primary key which are not supported."
    return pk_columns[0]


def guess_field_type(model_class: type, pk_field: str) -> typing.Callable:
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
    raise ValueError(f"Failed to guess primary key column caster for {column} (type={column.type}).")


class SADataSource(DataSource[T]):
    def __init__(
        self,
        model_class: typing.Type[T],
        query: sa.Select[tuple[T]] | None = None,
        query_for_list: sa.Select[tuple[T]] | None = None,
        pk_column: str | None = None,
        pk_cast: typing.Callable[[typing.Any], typing.Any] | None = None,
        _stmt: sa.Select[tuple[T]] | None = None,
    ) -> None:
        self.pk_column = pk_column or guess_pk_field(model_class)
        self.pk_cast = pk_cast or guess_field_type(model_class, self.pk_column)
        self.model_class = model_class

        self.query = query if query is not None else sa.select(model_class)
        self.query_for_list = query_for_list if query_for_list is not None else self.query

        self._stmt = _stmt if _stmt is not None else self.query

    def get_id_field(self) -> str:
        return self.pk_column

    def order_by(self, sorting: typing.Mapping[str, SortingType]) -> typing.Self:
        stmt = self._stmt.order_by(None)
        props = get_column_properties(self.model_class, list(sorting.keys()))

        for ordering_field, ordering_dir in sorting.items():
            try:
                prop = props[ordering_field]
                if len(prop.columns) > 1:  # pragma: no cover
                    continue
                column = prop.columns[0]
                stmt = stmt.order_by(column.desc() if ordering_dir == "desc" else column.asc())
            except KeyError:
                # ordering_field does not exist in properties, ignore
                continue
        return self._clone(stmt)

    def filter_clause(self, clause: ValueFilter) -> sa.ColumnElement[bool]:
        column: sa.sql.ColumnElement = getattr(self.model_class, clause.field)
        match clause:
            # string operations
            case StringFilter(value=value, predicate=StringOperation.STARTSWITH, case_insensitive=case_insensitive):
                return column.istartswith(value) if case_insensitive else column.startswith(value)
            case StringFilter(value=value, predicate=StringOperation.ENDSWITH, case_insensitive=case_insensitive):
                return column.iendswith(value) if case_insensitive else column.endswith(value)
            case StringFilter(value=value, predicate=StringOperation.CONTAINS, case_insensitive=case_insensitive):
                return column.icontains(value) if case_insensitive else column.contains(value)
            case StringFilter(value=value, predicate=StringOperation.MATCHES):
                return column.regexp_match(value)
            case StringFilter(value=value, predicate=StringOperation.EXACT):
                return column == value

            # number operations
            case NumberFilter(value=value, predicate=NumberOperation.GREATER):
                return column > value
            case NumberFilter(value=value, predicate=NumberOperation.GREATER_OR_EQUAL):
                return column >= value
            case NumberFilter(value=value, predicate=NumberOperation.EQUALS):
                return column == value
            case NumberFilter(value=value, predicate=NumberOperation.LESS):
                return column < value
            case NumberFilter(value=value, predicate=NumberOperation.LESS_OR_EQUAL):
                return column <= value

            # date operations
            case DateFilter(value=value, predicate=DateOperation.EQUALS):
                expr = column if isinstance(clause, DateTimeFilter) else sa.func.date(column)
                return expr == value
            case DateFilter(value=value, predicate=DateOperation.AFTER):
                expr = column if isinstance(clause, DateTimeFilter) else sa.func.date(column)
                return expr >= value
            case DateFilter(value=value, predicate=DateOperation.BEFORE):
                expr = column if isinstance(clause, DateTimeFilter) else sa.func.date(column)
                return expr <= value

            # array operations
            case InFilter(values=values):
                field_type = guess_field_type(self.model_class, clause.field)
                return column.in_([field_type(v) for v in values])

            case _:
                raise AttributeError("Unsupported filter type.")

    def filter(self, clause: QueryFilter) -> typing.Self:
        match clause:
            # complex operations
            case AndFilter(filters=filters):
                return self._clone(self._stmt.where(sa.and_(*[self.filter_clause(f) for f in filters])))
            case OrFilter(filters=filters):
                return self._clone(self._stmt.where(sa.or_(*[self.filter_clause(f) for f in filters])))
            case _:
                return self._clone(self._stmt.where(self.filter_clause(clause)))

    def get_query_for_list(self) -> typing.Self:
        return self._clone(self.query_for_list)

    async def count(self, request: Request) -> int:
        stmt = sa.select(sa.func.count("*")).select_from(self._stmt)
        result = await get_dbsession(request).scalars(stmt)
        return result.one()

    async def one(self, request: Request) -> int:
        try:
            result = await get_dbsession(request).scalars(self._stmt)
            return result.one()
        except NoResultFound:
            raise NoObjectError()

    async def update(self, request: Request, instance: T) -> None:
        await get_dbsession(request).commit()

    async def create(self, request: Request, instance: T) -> None:
        try:
            get_dbsession(request).add(instance)
            await get_dbsession(request).commit()
        except IntegrityError as ex:
            if "duplicate key" in str(ex):
                raise DuplicateError()
            raise

    async def delete(self, request: Request, instance: T) -> None:
        await get_dbsession(request).delete(instance)
        await get_dbsession(request).commit([instance])

    async def delete_all(self, request: Request) -> None:
        delete_stmt = sa.delete(self.model_class).where(self._stmt.whereclause)
        await get_dbsession(request).execute(delete_stmt)
        await get_dbsession(request).commit()

    async def new(self) -> T:
        return self.model_class()

    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[T]:
        row_count = await self.count(request)

        offset = (page - 1) * page_size
        stmt = self._stmt.limit(page_size).offset(offset)
        result = await get_dbsession(request).scalars(stmt)
        rows = result.all()
        return Pagination(rows=list(rows), total_rows=row_count, page=page, page_size=page_size)

    def get_pk(self, obj: T) -> str:
        return str(getattr(obj, self.pk_column))

    def _clone(self, stmt: sa.Select | None = None) -> typing.Self:
        return self.__class__(
            query=self.query,
            model_class=self.model_class,
            query_for_list=self.query_for_list,
            _stmt=stmt if stmt is not None else self._stmt,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return repr(self._stmt)


async def load_choices(
    dbsession: AsyncSession,
    field: wtforms.SelectField,
    stmt: sa.Select,
    value_attr: str | typing.Callable[[typing.Any], str] = "id",
    label_attr: str | typing.Callable[[typing.Any], str] = str,
    empty_choice: bool = True,
    empty_choice_label: str = "",
) -> None:
    def callback(obj: object, attr: str) -> str:
        return getattr(obj, attr)

    value_getter = value_attr if callable(value_attr) else functools.partial(callback, attr=value_attr)
    label_getter = label_attr if callable(label_attr) else functools.partial(callback, attr=label_attr)

    rows = await dbsession.execute(stmt)
    field.choices = [(value_getter(row), label_getter(row)) for row in rows.scalars()]
    if empty_choice:
        field.choices.insert(0, ("", empty_choice_label))


def form_choices_from(
    model_class: typing.Any,
    value_attr: str | typing.Callable[[typing.Any], str] = "id",
    label_attr: str | typing.Callable[[typing.Any], str] = str,
    query: sa.Select | None = None,
    empty_choice: bool = True,
    empty_choice_label: str = "",
) -> typing.Any:
    query = query or sa.select(model_class)

    def callback(obj: object, attr: str) -> str:
        return getattr(obj, attr)

    value_getter = value_attr if callable(value_attr) else functools.partial(callback, attr=value_attr)
    label_getter = label_attr if callable(label_attr) else functools.partial(callback, attr=label_attr)

    async def loader(request: Request) -> typing.Sequence[tuple[typing.Any, str]]:
        result = await request.state.dbsession.scalars(query)
        choices: list[tuple[typing.Any, str]] = []
        if empty_choice:
            choices.append(("", empty_choice_label))
        for row in result:
            choices.append((value_getter(row), label_getter(row)))
        return choices

    return loader
