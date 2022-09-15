import sqlalchemy as sa
import typing
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import BaseRoute, Route, Router
from starlette.types import Receive, Scope, Send

from ohmyadmin.actions import Action, LinkAction, SubmitAction
from ohmyadmin.batch_actions import BatchAction, DeleteAllAction
from ohmyadmin.filters import BaseFilter, FilterIndicator, OrderingFilter, SearchFilter
from ohmyadmin.flash import flash
from ohmyadmin.forms import Form, HandlesFiles
from ohmyadmin.globals import globalize_dbsession
from ohmyadmin.helpers import render_to_response
from ohmyadmin.i18n import _
from ohmyadmin.layout import EmptyState, FormElement, Grid, Layout
from ohmyadmin.metrics import Metric
from ohmyadmin.pagination import Page
from ohmyadmin.responses import RedirectResponse, Response
from ohmyadmin.storage import FileStorage
from ohmyadmin.tables import (
    Column,
    LinkRowAction,
    RowAction,
    SortingHelper,
    get_page_size_value,
    get_page_value,
    get_search_value,
)

ResourceAction = typing.Literal['list', 'create', 'edit', 'delete', 'bulk']
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
    id: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    label_plural: typing.ClassVar[str] = ''
    icon: typing.ClassVar[str] = ''

    # orm configuration
    entity_class: typing.ClassVar[typing.Any] = None
    queryset: sa.sql.Select | None = None

    # table settings
    filters: typing.Iterable[typing.Type[BaseFilter]] | None = None
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
        super().__init__(routes=list(self.get_routes()))

    @property
    def searchable(self) -> bool:
        return any([column.searchable for column in self.get_table_columns()])

    @property
    def pk_column(self) -> str:
        for column in vars(self.entity_class).values():
            if hasattr(column, 'primary_key') and column.primary_key:
                return column.name

        raise ValueError(
            f'Could not determine automatically primary key column for resource {self.__class__.__name__}. '
            f'Please, specify it manually via Resource.pk_column attribute.'
        )

    @property
    def pk_type(self) -> typing.Type[PkType]:
        column = getattr(self.entity_class, self.pk_column)
        match column.type:
            case sa.Integer():
                return int
            case sa.String():
                return str
        return int

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

    def get_filters(self) -> typing.Iterable[BaseFilter]:
        table_columns = self.get_table_columns()
        columns = list([column for column in table_columns if column.searchable])
        yield SearchFilter(query_param=self.search_param, entity_class=self.entity_class, columns=columns)

        columns = [column for column in table_columns if column.sortable]
        yield OrderingFilter(entity_class=self.entity_class, columns=columns, query_param=self.ordering_param)

        filter_classes = self.filters or []
        for filter_class in filter_classes:
            yield filter_class()

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

    def get_default_form_actions(self, request: Request) -> typing.Iterable[Action]:
        yield SubmitAction(_('Save'), color='primary', name='_save')
        yield SubmitAction(_('Save and return to list'), name='_list')
        yield SubmitAction(_('Save and add new'), name='_add')

    def get_form_actions(self, request: Request) -> typing.Iterable[Action]:
        yield from self.form_actions or []
        yield from self.get_default_form_actions(request)

    def get_form_class(self) -> typing.Type[Form]:
        assert self.form_class, f'{self.__class__.__name__} must define form_class attribute.'
        return self.form_class

    def get_form_layout(self, request: Request, form: Form) -> Layout:
        return Grid(columns=2, children=[FormElement(field) for field in form])

    def get_empty_object(self) -> typing.Any:
        assert self.entity_class, 'entity_class is a mandatory attribute.'
        return self.entity_class()

    async def get_object(self, request: Request, session: AsyncSession, pk: int | str) -> typing.Any:
        column = getattr(self.entity_class, self.pk_column)
        stmt = self.get_queryset(request).limit(2).where(column == pk)
        result = await session.scalars(stmt)
        return result.unique().one()

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
        queryset = self.get_queryset(request)

        # apply filters
        filters = list(self.get_filters())
        indicators: list[FilterIndicator] = []
        visual_filters: list[BaseFilter] = []
        for filter_ in filters:
            queryset = await filter_.dispatch(request, queryset)
            indicators.extend(filter_.indicators)
            if filter_.has_ui:
                visual_filters.append(filter_)

        objects = await self.paginate_queryset(request, request.state.dbsession, queryset)
        search_query = get_search_value(request, self.search_param)

        # show empty table if no results and search or filters used, otherwise render empty state
        has_results = objects or search_query or indicators

        return render_to_response(
            request,
            self.index_view_template,
            {
                'resource': self,
                'objects': objects,
                'filters': visual_filters,
                'indicators': indicators,
                'page_has_results': has_results,
                'page_title': self.label_plural,
                'columns': self.get_table_columns(),
                'search_placeholder': self.search_placeholder,
                'sorting_helper': SortingHelper(self.ordering_param),
                'search_query': search_query,
                'empty_state': self.get_empty_state(request),
                'batch_actions': list(self.get_batch_actions()),
                'row_actions': list(self.get_row_actions(request)),
                'table_actions': list(self.get_table_actions(request)),
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

            form_class = self.get_form_class()
            form = await form_class.from_request(request, instance=instance)
            layout = self.get_form_layout(request, form)

            if await form.validate_on_submit(request):
                for field in form:
                    if isinstance(field, HandlesFiles):
                        assert file_store, _('Cannot save uploaded file because file storage is not configured.')
                        setattr(field, 'data', await field.save(file_store, instance))

                form.populate_obj(instance)
                await session.commit()
                flash(request).success(self.message_object_saved.format(label=self.label))
                return await self._detect_post_save_action(request, instance)

            object_label = str(instance) if pk else self.label
            label_template = self.edit_page_label if pk else self.create_page_label

            return render_to_response(
                request,
                self.edit_view_template,
                {
                    'form': form,
                    'layout': layout,
                    'request': request,
                    'form_actions': self.get_form_actions(request),
                    'page_title': label_template.format(resource=object_label),
                },
            )

    async def delete_object_view(self, request: Request) -> Response:
        async with self.dbsession() as session:
            instance = await self.get_object(request, session, pk=request.path_params['pk'])
            if not instance:
                raise HTTPException(404, _('Object does not exists.'))

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

    @classmethod
    def get_route_name(cls, action: ResourceAction) -> str:
        return f'resource_{cls.id}_{action}'

    @classmethod
    def get_bulk_route_name(cls, bulk_action: BatchAction) -> str:
        return cls.get_route_name('bulk') + '_' + bulk_action.id

    def get_routes(self) -> typing.Iterable[BaseRoute]:
        mapping = {int: 'int', str: 'str'}
        param_type = mapping[self.pk_type]

        yield Route('/', self.list_objects_view, methods=['GET', 'POST'], name=self.get_route_name('list'))
        yield Route('/new', self.edit_object_view, methods=['GET', 'POST'], name=self.get_route_name('create'))
        yield Route(
            '/{pk:%s}/edit' % param_type,
            self.edit_object_view,
            methods=['GET', 'POST'],
            name=self.get_route_name('edit'),
        )
        yield Route(
            '/{pk:%s}/delete' % param_type,
            self.delete_object_view,
            methods=['GET', 'POST'],
            name=self.get_route_name('delete'),
        )

        for bulk_action in self.get_batch_actions():
            yield Route(
                f'/bulk/{bulk_action.id}',
                bulk_action,
                methods=['GET', 'POST'],
                name=self.get_bulk_route_name(bulk_action),
            )

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
            with globalize_dbsession(session):
                scope.setdefault('state', {})
                scope['state']['dbsession'] = session
                scope['state']['resource'] = self
                await super().__call__(scope, receive, send)
                await session.commit()
