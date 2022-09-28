import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.orm import DeclarativeMeta, InstrumentedAttribute
from starlette.requests import Request

from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Page
from ohmyadmin.resources import ListState, Resource


class SQLAlchemyResource(Resource):
    queryset: sa.sql.Select
    entity_class: typing.ClassVar[typing.Type[DeclarativeMeta]]

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
        stmt = self.apply_search(stmt, state.search_term)
        stmt = self.apply_ordering(stmt, state.ordering)
        paged_stmt = self.apply_pagination(stmt, page_number=state.page, page_size=state.page_size)
        row_count = await self.get_object_count(request, stmt)
        result = await request.state.dbsession.scalars(paged_stmt)
        rows = result.all()
        return Page(rows=list(rows), total_rows=row_count, page=state.page, page_size=state.page_size)

    def apply_ordering(self, stmt: sa.sql.Select, ordering: dict[str, SortingType]) -> sa.sql.Select:
        return stmt

    def apply_search(self, stmt: sa.sql.Select, search_term: str) -> sa.sql.Select:
        return stmt

    def apply_pagination(self, stmt: sa.sql.Select, page_number: int, page_size: int) -> sa.sql.Select:
        offset = (page_number - 1) * page_size
        return stmt.limit(page_size).offset(offset)

    def create_form_class(self) -> typing.Type[wtforms.Form]:
        pass
