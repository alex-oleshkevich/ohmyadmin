import itertools
import sqlalchemy as sa
import typing
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import BaseRoute, Route, Router
from starlette.types import Receive, Scope, Send
from wtforms.fields.core import UnboundField

from ohmyadmin.actions import Action, LinkAction, SubmitAction
from ohmyadmin.flash import flash
from ohmyadmin.forms import EmptyState, Field, Form, FormField, Grid, HandlesFiles, Layout
from ohmyadmin.helpers import render_to_response
from ohmyadmin.i18n import _
from ohmyadmin.metrics import Metric
from ohmyadmin.pagination import Page
from ohmyadmin.responses import RedirectResponse, Response
from ohmyadmin.storage import FileStorage
from ohmyadmin.tables import (
    BaseFilter,
    BatchAction,
    Column,
    DeleteAllAction,
    LinkRowAction,
    OrderingFilter,
    RowAction,
    SearchFilter,
    SortingHelper,
    get_page_size_value,
    get_page_value,
    get_search_value,
)

ResourceAction = typing.Literal['list', 'create', 'edit', 'delete', 'batch_action']
PkType = int | str


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
    icon: str = ''
    pk_type: typing.Type[PkType] = int
    pk_column: str = 'id'

    # orm configuration
    entity_class: typing.Any | None = None
    queryset: sa.sql.Select | None = None

    # table settings
    filters: typing.Iterable[BaseFilter] | None = None
    table_columns: typing.Iterable[Column] | None = None
    batch_actions: typing.Iterable[BatchAction] | None = None
    table_actions: typing.Iterable[Action] | None = None
    row_actions: typing.Iterable[RowAction] | None = None
    metrics: typing.Iterable[Metric] | None = None

    # pagination and default filters
    page_param: str = 'page'
    page_size: int = 25
    page_sizes: list[int] | tuple[int, ...] | None = (25, 50, 75)
    page_size_param: str = 'page_size'
    search_param: str = 'search'
    ordering_param: str = 'ordering'
    search_placeholder: str = _('Search...')

    # form settings
    form_class: typing.Type[Form] | None = None
    form_fields: typing.Iterable[Field] | None = None
    form_actions: typing.Iterable[Action] | None = None
    create_page_label: str = _('Create {resource}')
    edit_page_label: str = _('Edit {resource}')
    delete_page_label: str = _('Delete {resource}')

    # templates
    index_view_template: str = 'ohmyadmin/table.html'
    edit_view_template: str = 'ohmyadmin/form.html'
    delete_view_template: str = 'ohmyadmin/delete.html'

    message_object_saved: str = _('{label} has been saved.')

    def __init__(self, sa_engine: AsyncEngine) -> None:
        self.dbsession = sessionmaker(sa_engine, expire_on_commit=False, class_=AsyncSession)
        super().__init__(routes=self.get_routes())

    @property
    def searchable(self) -> bool:
        return any([column.searchable for column in self.get_table_columns()])

    def get_empty_state(self, request: Request) -> Layout:
        return EmptyState(
            heading=_('Empty page'),
            message=_('This page currently has no data.'),
            actions=list(self.get_default_table_actions(request)),
        )

    def get_pk_value(self, entity: typing.Any) -> int | str:
        return getattr(entity, self.pk_column)

    def get_table_columns(self) -> typing.Iterable[Column]:
        assert self.table_columns is not None, 'Resource must define columns for table view.'
        return self.table_columns

    def get_queryset(self, request: Request) -> sa.sql.Select:
        assert self.entity_class is not None, 'entity_class must be defined on resource.'
        if self.queryset is not None:
            return self.queryset
        return sa.select(self.entity_class)

    # region: list
    def get_filters(self) -> typing.Iterable[BaseFilter]:
        filters = list(self.filters or []).copy()
        table_columns = self.get_table_columns()

        # attach ordering filter
        if sortables := [column.sort_by for column in table_columns if column.sortable]:
            filters.append(OrderingFilter(sortables, self.ordering_param))

        # make search filter
        if searchables := list(itertools.chain.from_iterable([c.search_in for c in table_columns if c.searchable])):
            filters.append(SearchFilter(columns=searchables, query_param=self.search_param))

        return filters

    def apply_filters(self, request: Request, stmt: sa.sql.Select) -> sa.sql.Select:
        for filter in self.get_filters():
            stmt = filter.apply(request, stmt)
        return stmt

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

    def get_default_batch_actions(self) -> typing.Iterable[BatchAction]:
        yield DeleteAllAction()

    def get_batch_actions(self) -> typing.Iterable[BatchAction]:
        yield from self.get_default_batch_actions()
        yield from self.batch_actions or []

    def get_metrics(self) -> typing.Iterable[Metric]:
        yield from self.metrics or []

    # endregion

    # region: form
    def get_default_form_actions(self, request: Request) -> typing.Iterable[Action]:
        yield SubmitAction(_('Save'), color='primary', name='_save')
        yield SubmitAction(_('Save and return to list'), name='_list')
        yield SubmitAction(_('Save and add new'), name='_add')

    def get_form_actions(self, request: Request) -> typing.Iterable[Action]:
        yield from self.form_actions or []
        yield from self.get_default_form_actions(request)

    def get_form_fields(self, request: Request) -> typing.Iterable[UnboundField]:
        assert (
            self.form_fields
        ), f'At least form_fields attribute must be defined on {self.__class__.__name__} resource.'
        return self.form_fields

    def get_form_class(self, request: Request) -> typing.Type[Form]:
        return Form.from_fields(self.get_form_fields(request), name=f'{self.__class__.__name__}EditForm')

    def get_form_layout(self, request: Request, form: Form) -> Layout:
        return Grid(cols=2, children=[FormField(field) for field in form])

    # endregion

    def get_empty_object(self) -> typing.Any:
        assert self.entity_class, 'entity_class is a mandatory attribute.'
        return self.entity_class()

    async def get_object(self, request: Request, session: AsyncSession, pk: int | str) -> typing.Any:
        column = getattr(self.entity_class, self.pk_column)
        stmt = self.get_queryset(request).limit(2).where(column == pk)
        result = await session.scalars(stmt)
        return result.one()

    async def get_object_count(self, session: AsyncSession, queryset: sa.sql.Select) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(queryset)
        result = await session.scalars(stmt)
        return result.one()

    async def get_objects(self, session: AsyncSession, queryset: sa.sql.Select) -> typing.Iterable:
        result = await session.scalars(queryset)
        return result.all()

    async def paginate_queryset(self, request: Request, session: AsyncSession, queryset: sa.sql.Select) -> Page:
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, list(self.page_sizes or []), self.page_size)
        offset = (page_number - 1) * page_size

        row_count = await self.get_object_count(session, queryset)
        queryset = queryset.limit(page_size).offset(offset)
        rows = await self.get_objects(session, queryset)
        return Page(rows=list(rows), total_rows=row_count, page=page_number, page_size=page_size)

    async def list_objects_view(self, request: Request) -> Response:
        async with self.dbsession() as session:
            if '_batch_action' in request.query_params:
                return await self.batch_action_view(request, request.query_params['_batch_action'])

            queryset = self.get_queryset(request)
            queryset = self.apply_filters(request, queryset)
            objects = await self.paginate_queryset(request, session, queryset)

            return render_to_response(
                request,
                self.index_view_template,
                {
                    'resource': self,
                    'objects': objects,
                    'page_title': self.label_plural,
                    'sorting_helper': SortingHelper(self.ordering_param),
                    'search_placeholder': self.search_placeholder,
                    'search_query': get_search_value(request, self.search_param),
                    'columns': self.get_table_columns(),
                    'row_actions': list(self.get_row_actions(request)),
                    'batch_actions': list(self.get_batch_actions()),
                    'table_actions': list(self.get_table_actions(request)),
                    'empty_state': self.get_empty_state(request),
                    'metrics': [await metric.render(request) for metric in self.get_metrics()],
                },
            )

    async def edit_object_view(self, request: Request) -> Response:
        file_store: FileStorage = request.state.file_storage
        pk = request.path_params.get('pk', None)
        async with self.dbsession() as session:
            if pk:
                instance = await self.get_object(request, session, pk=request.path_params['pk'])
                if not instance:
                    raise HTTPException(404, _('Object does not exists.'))
            else:
                instance = self.get_empty_object()
                session.add(instance)

            form_class = self.get_form_class(request)
            form = await form_class.from_request(request, instance=instance)
            layout = self.get_form_layout(request, form)

            if await form.validate_on_submit(request):
                exclude_fields: list[str] = []

                # handle uploads
                for field in form:
                    if isinstance(field, HandlesFiles):
                        assert file_store, _('Cannot save uploaded file because file storage is not configured.')

                        exclude_fields.append(field.name)
                        if destinations := await field.save(file_store, instance):
                            method = getattr(instance, f'add_file_paths_for_{field.name}')
                            method(*map(str, destinations))

                form.populate_obj(instance, exclude=exclude_fields)
                await session.commit()
                flash(request).success(self.message_object_saved.format(label=self.label))
                return await self._detect_post_save_action(request, instance)

            label_template = self.edit_page_label if pk else self.create_page_label

            return render_to_response(
                request,
                self.edit_view_template,
                {
                    'form': form,
                    'layout': layout,
                    'request': request,
                    'form_actions': self.get_form_actions(request),
                    'page_title': label_template.format(resource=self.label),
                },
            )

    async def delete_object_view(self, request: Request) -> Response:
        async with self.dbsession() as session:
            instance = await self.get_object(request, session, pk=request.path_params['pk'])
            if not instance:
                raise HTTPException(404, 'Object does not exists.')

            if request.method == 'POST':
                await session.delete(instance)
                await session.commit()
                return RedirectResponse(request).to_resource(self)

            return render_to_response(
                request,
                self.delete_view_template,
                {
                    'request': request,
                    'object': instance,
                    'page_title': self.delete_page_label.format(resource=self.label),
                },
            )

    async def batch_action_view(self, request: Request, action_id: str) -> Response:
        batch_action = next((action for action in self.get_batch_actions() if action.id == action_id))
        if not batch_action:
            return RedirectResponse(request).to_resource(self).with_error(_('Unknown batch action.'))

        if request.method == 'POST':
            form_data = await request.form()
            object_ids = [self.pk_type(object_id) for object_id in form_data.getlist('selected')]
            return await batch_action.apply(request, object_ids, form_data)

        return Response(batch_action.render())

    @classmethod
    def get_route_name(cls, action: ResourceAction) -> str:
        return f'resource_{cls.id}_{action}'

    def get_routes(self) -> typing.Sequence[BaseRoute]:
        mapping = {int: 'int', str: 'str'}
        param_type = mapping[self.pk_type]

        return [
            Route('/', self.list_objects_view, methods=['GET', 'POST'], name=self.get_route_name('list')),
            Route('/new', self.edit_object_view, methods=['GET', 'POST'], name=self.get_route_name('create')),
            Route(
                '/{pk:%s}/edit' % param_type,
                self.edit_object_view,
                methods=['GET', 'POST'],
                name=self.get_route_name('edit'),
            ),
            Route(
                '/{pk:%s}/delete' % param_type,
                self.delete_object_view,
                methods=['GET', 'POST'],
                name=self.get_route_name('delete'),
            ),
        ]

    async def _detect_post_save_action(self, request: Request, instance: typing.Any) -> Response:
        form_data = await request.form()
        pk = self.get_pk_value(instance)
        if '_save' in form_data:
            return RedirectResponse(request).to_resource(self, 'edit', pk=pk)
        if '_add' in form_data:
            return RedirectResponse(request).to_resource(self, 'create')
        if '_list' in form_data:
            return RedirectResponse(request).to_resource(self)
        raise ValueError('Could not determine redirect route.')

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self.dbsession() as session:
            scope.setdefault('state', {})
            scope['state']['dbsession'] = session
            scope['state']['resource'] = self
            await super().__call__(scope, receive, send)
            await session.commit()
