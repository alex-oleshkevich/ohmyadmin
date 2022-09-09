import sqlalchemy as sa
import typing
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route, Router
from starlette.types import Receive, Scope, Send

from ohmyadmin.actions import Action, LinkAction
from ohmyadmin.forms import Field
from ohmyadmin.i18n import _
from ohmyadmin.tables import BaseFilter, BatchAction, Column, LinkRowAction, RowAction, TableView


def label_from_resource_class(class_name: str) -> str:
    return class_name.removesuffix('Resource').title()


class ResourceMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        attrs['id'] = attrs.get('id', name.removesuffix('Resource').lower())
        attrs['label'] = attrs.get('label', name.removesuffix('Resource').title())
        attrs['label_plural'] = attrs.get('label_plural', attrs['label'] + 's')
        return super().__new__(cls, name, bases, attrs)


class Resource(Router, metaclass=ResourceMeta):
    id: str = ''
    label: str = ''
    label_plural: str = ''
    queryset: sa.sql.Select | None = None

    # table settings
    filters: typing.Iterable[BaseFilter] | None = None
    table_columns: typing.Iterable[Column] | None = None
    batch_actions: typing.Iterable[BatchAction] | None = None
    table_actions: typing.Iterable[Action] | None = None
    row_actions: typing.Iterable[RowAction] | None = None
    table_view_class: typing.Type[TableView] = TableView

    page_param: str = 'page'
    page_size: int = 25
    page_sizes: list[int] | None = None
    page_size_param: str = 'page_size'
    search_param: str = 'search'
    ordering_param: str = 'ordering'
    search_placeholder: str = _('Search...')

    # form settings
    edit_form: typing.Iterable[Field] | None = None
    create_form: typing.Iterable[Field] | None = None
    form_actions: typing.Iterable[Action] | None = None

    # templates
    index_view_template: str = 'ohmyadmin/table.html'

    def __init__(self, dbsession: sessionmaker) -> None:
        self.dbsession = dbsession
        super().__init__(routes=self.get_routes())

    def get_pk_value(self, entity: typing.Any) -> int | str:
        return entity.id

    def get_queryset(self, request: Request) -> sa.sql.Select:
        assert self.queryset is not None, 'Queryset must be defined on resource.'
        return self.queryset

    def get_table_columns(self, request: Request) -> typing.Iterable[Column]:
        assert self.table_columns is not None, 'Resource must define columns for table view.'
        return self.table_columns

    def get_default_table_actions(self, request: Request) -> typing.Iterable[Action]:
        yield LinkAction(
            url=request.url_for(self.get_route_name('create')),
            text=_('Add {resource}'.format(resource=self.label)),
            icon='plus',
            color='primary',
        )

    def get_table_actions(self, request: Request) -> typing.Iterable[Action]:
        yield from self.table_actions or []
        yield from self.get_default_table_actions(request)

    def get_default_row_actions(self, request: Request) -> typing.Iterable[RowAction]:
        yield LinkRowAction(
            lambda entity: request.url_for(self.get_route_name('edit'), pk=self.get_pk_value(entity)),
            icon='pencil',
        )
        yield LinkRowAction(
            lambda entity: request.url_for(self.get_route_name('delete'), pk=self.get_pk_value(entity)),
            icon='trash',
            color='danger',
        )

    def get_row_actions(self, request: Request) -> typing.Iterable[RowAction]:
        yield from self.row_actions or []
        yield from self.get_default_row_actions(request)

    def get_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        yield from self.batch_actions or []

    async def list_objects_view(self, request: Request) -> Response:
        async with self.dbsession() as session:
            table = self.table_view_class(
                session=session,
                page_size=self.page_size,
                page_param=self.page_param,
                search_param=self.search_param,
                columns=self.get_table_columns(request),
                ordering_param=self.ordering_param,
                queryset=self.get_queryset(request),
                page_size_param=self.page_size_param,
                search_placeholder=self.search_placeholder,
                page_sizes=self.page_sizes or [25, 50, 75, 100],
                label=self.label_plural,
                row_actions=self.get_row_actions(request),
                table_actions=self.get_table_actions(request),
                batch_actions=self.get_batch_actions(request),
                template=self.index_view_template,
            )
            return await table.dispatch(request)

    def create_object_view(self, request: Request) -> Response:
        return Response('create')

    def edit_object_view(self, request: Request) -> Response:
        return Response('edit')

    def delete_object_view(self, request: Request) -> Response:
        return Response('delete')

    @classmethod
    def get_route_name(cls, action: typing.Literal['list', 'create', 'edit', 'delete']) -> str:
        return f'resource_{cls.id}_{action}'

    def get_routes(self) -> typing.Sequence[BaseRoute]:
        return [
            Route('/', self.list_objects_view, name=self.get_route_name('list')),
            Route('/new', self.create_object_view, methods=['GET', 'POST'], name=self.get_route_name('create')),
            Route('/edit/{pk}', self.edit_object_view, methods=['GET', 'POST'], name=self.get_route_name('edit')),
            Route('/delete/{pk}', self.delete_object_view, methods=['GET', 'POST'], name=self.get_route_name('delete')),
        ]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self.dbsession() as session:
            scope.setdefault('state', {})
            scope['state']['dbsession'] = session
            return await super().__call__(scope, receive, send)
