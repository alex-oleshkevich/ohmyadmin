import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.orm import DeclarativeMeta, InstrumentedAttribute
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.actions import BatchAction
from ohmyadmin.components import ButtonColor
from ohmyadmin.i18n import _
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Page
from ohmyadmin.resources import ListState, Resource


class SQLAlchemyResource(Resource):
    queryset: sa.sql.Select
    entity_class: typing.ClassVar[typing.Any]

    def get_pk_column(self) -> InstrumentedAttribute:
        mapper = sa.orm.class_mapper(self.get_entity_class())
        keys = [mapper.get_property_by_column(c) for c in mapper.primary_key]
        column = keys[0].columns[0]
        return column

    def get_pk_value(self, entity: typing.Any) -> str:
        return getattr(entity, self.get_pk_column().key)

    def get_route_pk_type(self) -> str:
        pk_column = self.get_pk_column()
        match pk_column:
            case sa.Column(type=sa.Integer()):
                return 'int'
            case sa.Column(type=sa.String()):
                return 'str'
        raise ValueError(f'Cannot get route parameter type from primary key column {pk_column}.')

    def get_entity_class(self) -> typing.Type[DeclarativeMeta]:
        entity_class = getattr(self, 'entity_class', None)
        if not entity_class:
            raise AttributeError(f'{self.__class__.__name__} must define entity_class attribute.')
        return entity_class

    def create_new_entity(self) -> typing.Any:
        return self.get_entity_class()

    async def save_entity(self, request: Request, form: wtforms.Form, instance: typing.Any) -> None:
        form.populate_obj(instance)
        request.state.dbsession.add(instance)
        await request.state.dbsession.commit()

    async def delete_entity(self, request: Request, instance: typing.Any) -> None:
        await request.state.dbsession.delete(instance)
        await request.state.dbsession.commit()

    def get_queryset(self, request: Request) -> sa.sql.Select:
        return getattr(self, 'queryset', sa.select(self.get_entity_class()))

    async def get_object(self, request: Request, pk: typing.Any) -> typing.Any | None:
        pk_column = self.get_pk_column()
        stmt = self.get_queryset(request).where(pk_column == pk)
        result = await request.state.dbsession.scalars(stmt)
        return result.one_or_none()

    async def get_object_count(self, request: Request, stmt: sa.sql.Select) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(stmt)
        result = await request.state.dbsession.scalars(stmt)
        return result.one()

    async def get_objects(self, request: Request, state: ListState) -> Page[typing.Any]:
        stmt = self.get_queryset(request)
        stmt = self.apply_search(stmt, state.search_term, state.searchable_fields)
        stmt = self.apply_ordering(stmt, state.ordering, state.sortable_fields)
        paged_stmt = self.apply_pagination(stmt, page_number=state.page, page_size=state.page_size)
        row_count = await self.get_object_count(request, stmt)
        result = await request.state.dbsession.scalars(paged_stmt)
        rows = result.all()
        return Page(rows=list(rows), total_rows=row_count, page=state.page, page_size=state.page_size)

    def apply_ordering(
        self, stmt: sa.sql.Select, ordering: dict[str, SortingType], sortable_fields: list[str]
    ) -> sa.sql.Select:
        if ordering:
            stmt = stmt.order_by(None)

        mapper = sa.orm.class_mapper(self.get_entity_class())
        props = [mapper.get_property_by_column(c) for c in mapper.columns if c.key in sortable_fields]
        for prop in props:
            if len(prop.columns) > 1:
                continue
            column = prop.columns[0]
            direction = ordering.get(prop.key)
            if direction:
                stmt = stmt.order_by(column.desc() if direction == 'desc' else column.asc())
        return stmt

    def apply_search(self, stmt: sa.sql.Select, search_term: str, searchable_fields: list[str]) -> sa.sql.Select:
        mapper = sa.orm.class_mapper(self.get_entity_class())
        props = [mapper.get_property_by_column(c) for c in mapper.columns if c.key in searchable_fields]
        clauses = []
        for prop in props:
            if len(prop.columns) > 1:
                continue
            clauses.append(self.create_search_token(prop.columns[0], search_term))

        return stmt.where(sa.or_(*clauses))

    def create_search_token(self, column: InstrumentedAttribute, search_query: str) -> sa.sql.ColumnElement:
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

    def apply_pagination(self, stmt: sa.sql.Select, page_number: int, page_size: int) -> sa.sql.Select:
        offset = (page_number - 1) * page_size
        return stmt.limit(page_size).offset(offset)

    def create_form_class(self) -> typing.Type[wtforms.Form]:
        pass


class BatchDeleteAction(BatchAction):
    icon = 'trash'
    color: ButtonColor = 'danger'
    dangerous = True
    confirmation = _('Do you wish to delete all selected records?')
    label = _('Batch delete')

    def __init__(self, entity_class: typing.Any, pk_column: InstrumentedAttribute) -> None:
        self.pk_column = pk_column
        self.entity_class = entity_class
        super().__init__(label=_('Batch delete'), icon='trash', color='danger')

    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        coalesce: typing.Callable = str
        match self.pk_column.expression.type:
            case sa.Integer():
                coalesce = int

        typed_ids = [coalesce(object_id) for object_id in object_ids]
        stmt = sa.select(self.entity_class).where(self.pk_column.in_(typed_ids))
        result = await request.state.dbsession.scalars(stmt)
        objects = result.all()

        for object in objects:
            await request.state.dbsession.delete(object)
        await request.state.dbsession.commit()
        return self.refresh()
