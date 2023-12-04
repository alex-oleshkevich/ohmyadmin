import decimal
import sqlalchemy as sa
import typing
import uuid
from sqlalchemy import orm
from starlette.requests import Request

from ohmyadmin.datasources.datasource import DataSource, SearchPredicate
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination

T = typing.TypeVar(
    'T',
)


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


class SADataSource(DataSource[T]):
    def __init__(
        self,
        model_class: typing.Type[T],
        query: sa.Select[T] | None = None,
        query_for_list: sa.Select[T] | None = None,
        pk_column: str | None = None,
        pk_cast: typing.Callable[[typing.Any], typing.Any] | None = None,
        _stmt: sa.Select[T] | None = None,
    ) -> None:
        self.pk_column = pk_column or guess_pk_field(model_class)
        self.pk_cast = pk_cast or guess_pk_type(model_class, self.pk_column)
        self.model_class = model_class
        self.query = query if query is not None else sa.select(model_class)
        self.query_for_list = query_for_list if query_for_list is not None else self.query
        self._stmt = _stmt if _stmt is not None else self.query

    def get_query_for_list(self) -> typing.Self:
        return self._clone(self.query_for_list)

    def apply_search_filter(self, term: str, predicate: SearchPredicate, fields: list[str]) -> typing.Self:
        if not term:
            return self._clone(self._stmt)

        clauses = []
        props = get_column_properties(self.model_class, fields)
        for prop in props.values():
            if len(prop.columns) > 1:  # pragma: no cover, no idea
                continue

            column = prop.columns[0]
            string_column = sa.cast(column, sa.Text)

            match predicate:
                case 'startswith':
                    clauses.append(sa.func.lower(string_column).startswith(term.lower()))
                case 'endswith':
                    clauses.append(sa.func.lower(string_column).endswith(term.lower()))
                case 'matches':
                    clauses.append(sa.func.lower(string_column).regexp_match(term.lower()))
                case 'exact':
                    clauses.append(string_column == term)
                case _:
                    clauses.append(string_column.ilike(f'%{term.lower()}%'))

        return self._clone(self._stmt.where(sa.or_(*clauses)))

    def apply_ordering_filter(self, rules: dict[str, SortingType], fields: typing.Sequence[str]) -> typing.Self:
        stmt = self._stmt.order_by(None)
        props = get_column_properties(self.model_class, fields)

        for ordering_field, ordering_dir in rules.items():
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

    async def count(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(self._stmt)
        result = await request.state.dbsession.scalars(stmt)
        return result.one()

    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[T]:
        row_count = await self.count(request)

        offset = (page - 1) * page_size
        stmt = self._stmt.limit(page_size).offset(offset)
        result = await request.state.dbsession.scalars(stmt)
        rows = result.all()
        return Pagination(rows=list(rows), total_rows=row_count, page=page, page_size=page_size)

    def _clone(self, stmt: sa.Select | None = None) -> typing.Self:
        return self.__class__(
            query=self.query,
            model_class=self.model_class,
            query_for_list=self.query_for_list,
            _stmt=stmt if stmt is not None else self._stmt,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return repr(self._stmt)
