import sqlalchemy as sa
import typing
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import BaseRoute, Route, Router
from starlette.types import Receive, Scope, Send

from ohmyadmin.actions import Action, BatchAction, BulkDeleteAction
from ohmyadmin.components import Button, ButtonLink, Component, EmptyState, FormElement, Grid, Row, RowAction
from ohmyadmin.filters import BaseFilter, FilterIndicator, OrderingFilter, SearchFilter
from ohmyadmin.flash import flash
from ohmyadmin.forms import Form, HandlesFiles
from ohmyadmin.helpers import camel_to_sentence, pluralize, render_to_response
from ohmyadmin.i18n import _
from ohmyadmin.metrics import Metric
from ohmyadmin.pages import PageMeta
from ohmyadmin.pagination import Page
from ohmyadmin.responses import RedirectResponse, Response
from ohmyadmin.storage import FileStorage
from ohmyadmin.structures import URLSpec
from ohmyadmin.tables import (
    ActionColumn,
    Column,
    RowActionsCallback,
    SortingHelper,
    get_page_size_value,
    get_page_value,
    get_search_value,
)

ResourceAction = typing.Literal['list', 'create', 'edit', 'delete', 'batch', 'action', 'metric']
PkType = int | str

_RowActionsArgs = typing.ParamSpec('_RowActionsArgs')
_RowActionsReturn = typing.TypeVar('_RowActionsReturn')


def wrap_row_actions(
    fn: typing.Callable[_RowActionsArgs, _RowActionsReturn],
) -> typing.Callable[typing.Concatenate['Resource', _RowActionsArgs], _RowActionsReturn]:
    def wrapper(self: 'Resource', *args: _RowActionsArgs.args, **kwargs: _RowActionsArgs.kwargs) -> _RowActionsReturn:
        return fn(*args, **kwargs)

    return wrapper


class ResourceMeta(PageMeta):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        if name != 'Resource':
            attrs['id'] = attrs.get('id', pluralize(slugify(name.removesuffix('Resource'))))
            attrs['label'] = attrs.get('label', camel_to_sentence(name.removesuffix('Resource')))
            attrs['label_plural'] = attrs.get('label_plural', pluralize(attrs['label']))

            if 'pk_column' not in attrs:
                for column in vars(attrs['entity_class']).values():
                    if hasattr(column, 'primary_key') and column.primary_key:
                        attrs['pk_column'] = column.name
                        break
                else:
                    raise ValueError(
                        f'Could not determine automatically primary key column for resource {name}. '
                        f'Please, specify it manually via Resource.pk_column attribute.'
                    )

        if 'row_actions' in attrs:
            # when lambda attached to a class it will receive self as the first argument
            # this adds undesired behavior so lets it in a function that transparently handles self argument
            attrs['row_actions'] = wrap_row_actions(attrs['row_actions']) if attrs['row_actions'] else None

        return super().__new__(cls, name, bases, attrs)


class Resource(Router, metaclass=ResourceMeta):
    id: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    label_plural: typing.ClassVar[str] = ''
    icon: typing.ClassVar[str] = ''

    # orm configuration
    entity_class: typing.ClassVar[typing.Any] = None
    queryset: typing.ClassVar[sa.sql.Select | None] = None
    pk_column: str

    # table settings
    filters: typing.ClassVar[typing.Iterable[typing.Type[BaseFilter]] | None] = None
    table_columns: typing.ClassVar[typing.Iterable[Column] | None] = None
    batch_actions: typing.ClassVar[typing.Iterable[BatchAction] | None] = None
    page_actions: typing.ClassVar[typing.Iterable[Component] | None] = None
    row_actions: typing.ClassVar[RowActionsCallback | None] = None
    metrics: typing.ClassVar[typing.Iterable[Metric] | None] = None

    # pagination and default filters
    page_param: str = 'page'
    page_size: int = 25
    page_sizes: list[int] | tuple[int, ...] | None = (25, 50, 75)
    page_size_param: str = 'page_size'
    search_param: str = 'search'
    ordering_param: str = 'ordering'
    search_placeholder: str = _('Search...')

    # form settings
    form_class: typing.ClassVar[typing.Type[Form] | None] = None
    form_actions: typing.ClassVar[typing.Iterable[Component] | None] = None
    create_page_label: str = _('Create {resource}')
    edit_page_label: str = _('Edit {resource}')
    delete_page_label: str = _('Delete {resource}')

    # templates
    index_view_template: str = 'ohmyadmin/table.html'
    edit_view_template: str = 'ohmyadmin/form.html'
    delete_view_template: str = 'ohmyadmin/delete.html'

    message_object_saved: str = _('{label} has been saved.')

    def __init__(self) -> None:
        super().__init__(routes=list(self.get_routes()))

    @property
    def searchable(self) -> bool:
        return any([column.searchable for column in self.get_table_columns()])

    @property
    def pk_type(self) -> typing.Type[PkType]:
        """Get primary key type."""
        column = getattr(self.entity_class, self.pk_column)
        match column.type:
            case sa.Integer():
                return int
            case sa.String():
                return str
        return int

    def get_empty_state(self) -> Component:
        """
        Return empty state component.

        Empty states used on pages that have no data (empty) and no filters
        applied.
        """

        return EmptyState(
            heading=_('Empty page'),
            message=_('This page currently has no data.'),
            actions=list(self.get_default_page_actions()),
        )

    def get_pk_value(self, entity: typing.Any) -> int | str:
        """Get primary key value from the entity."""

        return getattr(entity, self.pk_column)

    def get_table_columns(self) -> typing.Iterable[Column]:
        """Collect and return configured table columns."""

        assert self.table_columns is not None, 'Resource must define columns for table view.'
        yield from self.table_columns
        yield ActionColumn(self.get_row_actions)

    def get_queryset(self, request: Request) -> sa.sql.Select:
        """
        Get queryset.

        By default, it returns the Resource.queryset or raises.
        """

        assert self.entity_class is not None, 'entity_class must be defined on resource.'
        if self.queryset is not None:
            return self.queryset
        return sa.select(self.entity_class)

    def get_filters(self) -> typing.Iterable[BaseFilter]:
        """
        Get filters.

        If resource has searchable or orderable columns then SearchFilter and
        OrderingFilter will be added.
        """

        table_columns = list(self.get_table_columns())
        columns = list([column for column in table_columns if column.searchable])
        yield SearchFilter(query_param=self.search_param, entity_class=self.entity_class, columns=columns)

        columns = [column for column in table_columns if column.sortable]
        yield OrderingFilter(entity_class=self.entity_class, columns=columns, query_param=self.ordering_param)

        filter_classes = self.filters or []
        for filter_class in filter_classes:
            yield filter_class()

    def get_default_page_actions(self) -> typing.Iterable[Component]:
        """Return default index page actions."""

        yield ButtonLink(
            url=URLSpec(resource=self, resource_action='create'),
            text=_('Add {resource}'.format(resource=self.label)),
            icon='plus',
            color='primary',
        )

    def get_page_actions(self) -> typing.Iterable[Component]:
        """Return user defined index page actions."""
        yield from self.page_actions or []
        yield from self.get_default_page_actions()

    def get_default_row_actions(self, entity: typing.Any) -> typing.Iterable[Component]:
        yield RowAction(entity, icon='pencil', url=URLSpec.to_resource(self, 'edit', {'pk': self.get_pk_value(entity)}))
        yield RowAction(
            entity,
            icon='trash',
            url=URLSpec.to_resource(self, 'delete', {'pk': self.get_pk_value(entity)}),
            danger=True,
        )

    def get_row_actions(self, entity: typing.Any) -> typing.Iterable[Component]:
        yield from self.row_actions(entity) if callable(self.row_actions) else []
        yield from self.get_default_row_actions(entity)

    def get_default_batch_actions(self) -> typing.Iterable[BatchAction]:
        yield BulkDeleteAction()

    def get_batch_actions(self) -> typing.Iterable[BatchAction]:
        yield from self.get_default_batch_actions()
        yield from self.batch_actions or []

    def get_metrics(self) -> typing.Iterable[Metric]:
        yield from self.metrics or []

    def get_default_form_actions(self) -> typing.Iterable[Component]:
        yield Button(_('Save'), color='primary', name='_save')
        yield Button(_('Save and return to list'), name='_list')
        yield Button(_('Save and add new'), name='_add')

    def get_form_actions(self) -> typing.Iterable[Component]:
        yield from self.get_default_form_actions()
        yield from self.form_actions or []

    def get_form_class(self) -> typing.Type[Form]:
        assert self.form_class, f'{self.__class__.__name__} must define form_class attribute.'
        return self.form_class

    def get_form_layout(self, request: Request, form: Form) -> Component:
        return Grid(columns=1, children=[Row(children=[FormElement(field, colspan=6)], columns=12) for field in form])

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
                'columns': list(self.get_table_columns()),
                'search_placeholder': self.search_placeholder,
                'sorting_helper': SortingHelper(self.ordering_param),
                'search_query': search_query,
                'empty_state': self.get_empty_state(),
                'batch_actions': list(self.get_batch_actions()),
                'page_actions': list(self.get_page_actions()),
                'metrics': [
                    request.url_for(self.get_route_name('metric'), metric_id=metric.id) for metric in self.get_metrics()
                ],
            },
        )

    async def edit_object_view(self, request: Request) -> Response:
        file_store: FileStorage = request.state.file_storage
        pk = request.path_params.get('pk', None)
        session = request.state.dbsession
        if pk:
            instance = await self.get_object(request, session, pk=request.path_params['pk'])
            if not instance:
                raise HTTPException(404, _('Object does not exists.'))
        else:
            instance = self.get_empty_object()

        form_class = self.get_form_class()
        form = await form_class.from_request(request, instance=instance)
        layout = self.get_form_layout(request, form)
        fields_to_exclude: list[str] = []
        if await form.validate_on_submit(request):
            for field in form:
                if isinstance(field, HandlesFiles):
                    assert file_store, _('Cannot save uploaded file because file storage is not configured.')
                    fields_to_exclude.append(field.name)
                    if file_paths := await field.save(file_store, instance):
                        entity_method_name = f'add_file_paths_for_{field.name}'
                        entity_method = getattr(instance, entity_method_name, None)
                        if not entity_method:
                            raise AttributeError(
                                f'In order to process uploaded files, the model {instance.__class__.__name__} '
                                f'must define `{entity_method_name}(*file_paths: str) -> None` method. '
                            )
                        entity_method(*file_paths)

            form.populate_obj(instance, exclude=fields_to_exclude)
            if not pk:
                session.add(instance)
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
                'form_actions': self.get_form_actions(),
                'page_title': label_template.format(resource=object_label),
            },
        )

    async def delete_object_view(self, request: Request) -> Response:
        session = request.state.dbsession
        instance = await self.get_object(request, session, pk=request.path_params['pk'])
        if not instance:
            raise HTTPException(404, _('Object does not exists.'))

        if request.method == 'POST':
            await session.delete(instance)
            return (
                RedirectResponse(request)
                .to_resource(self)
                .with_success(_('{resource} has been deleted.'.format(resource=str(instance))))
            )

        return render_to_response(
            request,
            self.delete_view_template,
            {
                'request': request,
                'object': instance,
                'page_title': self.delete_page_label.format(resource=self.label),
            },
        )

    async def metric_view(self, request: Request) -> Response:
        """A backend for resource metric cards."""
        metric_id = request.path_params['metric_id']
        metric = next((metric for metric in self.get_metrics() if metric.id == metric_id))
        if not metric:
            raise HTTPException(404, 'Metric does not exists.')
        return await metric.dispatch(request)

    async def action_view(self, request: Request) -> Response:
        """A backend for standalone resource actions."""
        try:
            action_id = request.path_params['action_id']
            action = next(
                (action for action in self.get_page_actions() if isinstance(action, Action) and action.id == action_id)
            )
            return await action.dispatch(request)
        except StopIteration:
            raise HTTPException(404, 'Action does not exists.')

    async def batch_action_view(self, request: Request) -> Response:
        """A backend for batch resource actions."""
        try:
            action_id = request.path_params['action_id']
            action = next(
                (
                    action
                    for action in self.get_batch_actions()
                    if isinstance(action, BatchAction) and action.id == action_id
                )
            )
            return await action.dispatch(request)
        except StopIteration:
            raise HTTPException(404, 'Batch action does not exists.')

    @classmethod
    def get_route_name(cls, action: ResourceAction, sub_action: str | None = None) -> str:
        sub_action = f'_{sub_action}' if sub_action else ''
        return f'ohmyadmin_resource_{cls.id}_{action}{sub_action}'

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

        yield Route('/metric/{metric_id}', self.metric_view, name=self.get_route_name('metric'))
        yield Route(
            '/actions/{action_id}', self.action_view, methods=['GET', 'POST'], name=self.get_route_name('action')
        )
        yield Route(
            '/batch/{action_id}', self.batch_action_view, methods=['GET', 'POST'], name=self.get_route_name('batch')
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
        scope.setdefault('state', {})
        scope['state']['resource'] = self
        await super().__call__(scope, receive, send)
        await scope['state']['dbsession'].commit()
