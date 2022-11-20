from __future__ import annotations

import dataclasses

import abc
import typing
import wtforms
from slugify import slugify
from starlette.datastructures import URL
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Route, Router
from starlette.types import Receive, Scope, Send
from starlette_flash import flash

from ohmyadmin import layout
from ohmyadmin.actions import (
    Action,
    BatchAction,
    Dispatch,
    LinkAction,
    LinkRowAction,
    ModalRowAction,
    RowAction,
    RowActionGroup,
)
from ohmyadmin.display import DisplayField
from ohmyadmin.filters import BaseFilter
from ohmyadmin.forms import Form, Prefill
from ohmyadmin.helpers import camel_to_sentence, pluralize
from ohmyadmin.i18n import _
from ohmyadmin.layout import LayoutComponent
from ohmyadmin.metrics import Metric
from ohmyadmin.ordering import SortingHelper, SortingType, get_ordering_value
from ohmyadmin.pagination import Page, get_page_size_value, get_page_value
from ohmyadmin.projections import Projection
from ohmyadmin.templating import TemplateResponse, admin_context, render_to_string


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '').strip()


@dataclasses.dataclass
class ListState:
    page: int
    page_size: int
    search_term: str
    sortable_fields: list[str]
    searchable_fields: list[str]
    ordering: dict[str, SortingType]


@dataclasses.dataclass
class HeadCell:
    text: str
    sortable: bool
    index: int | None
    url: URL | None
    sorted: SortingType | None


class TableMixin:
    table_template = 'ohmyadmin/list_page/table.html'

    def render_table(self: Resource, request: Request, page: Page[typing.Any]) -> str:  # type:ignore[misc]
        sort_helper = SortingHelper(request, self.ordering_param)
        head_cells: list[HeadCell] = []
        for field in self.fields:
            head_cells.append(
                HeadCell(
                    text=field.label,
                    sortable=field.sortable,
                    url=sort_helper.get_url(field.sort_by),
                    index=sort_helper.get_current_ordering_index(field.sort_by),
                    sorted=sort_helper.get_current_ordering(field.sort_by),
                )
            )

        row_actions = list(self.get_configured_row_actions(request))
        batch_actions = list(self.get_configured_batch_actions(request))
        return render_to_string(
            self.table_template,
            {
                'objects': page,
                'request': request,
                'cells': self.fields,
                'header': head_cells,
                'pk': self.get_pk_value,
                'row_actions': row_actions,
                'batch_actions': batch_actions,
            },
        )


class ResourceMeta(type):
    def __new__(mcs, name: str, bases: tuple[typing.Type, ...], attrs: dict[str, typing.Any]) -> typing.Type:
        if '__abstract__' not in attrs:
            human_name = name.removesuffix('Resource')
            if 'slug' not in attrs:
                attrs['slug'] = slugify(pluralize(camel_to_sentence(human_name)))
            if 'label' not in attrs:
                attrs['label'] = camel_to_sentence(human_name)
            if 'label_plural' not in attrs:
                attrs['label_plural'] = pluralize(camel_to_sentence(human_name))

        return super().__new__(mcs, name, bases, attrs)


class Resource(TableMixin, Router, metaclass=ResourceMeta):
    __abstract__ = True

    icon: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    label_plural: typing.ClassVar[str] = ''
    group: typing.ClassVar[str] = 'Resources'
    slug: typing.ClassVar[str] = ''
    index_template: typing.ClassVar[str] = 'ohmyadmin/list.html'
    form_template: typing.ClassVar[str] = 'ohmyadmin/form.html'
    edit_template: typing.ClassVar[str] = form_template
    create_template: typing.ClassVar[str] = form_template
    delete_template: typing.ClassVar[str] = 'ohmyadmin/delete.html'
    form_class: typing.ClassVar[typing.Type[wtforms.Form] | None] = None
    page_param: typing.ClassVar[str] = 'page'
    page_size_param: typing.ClassVar[str] = 'page_size'
    search_param: typing.ClassVar[str] = 'search'
    ordering_param: typing.ClassVar[str] = 'ordering'
    page_size: typing.ClassVar[int] = 25
    max_page_size: typing.ClassVar[int] = 100
    page_title_for_create: str = _('Create {resource}')
    page_title_for_edit: str = _('Edit {entity}')
    page_title_for_delete: str = _('Delete {entity}?')

    def __init__(self) -> None:
        super().__init__(routes=list(self.get_routes()))
        self.fields = list(self.get_list_fields())

    @property
    def sortable_fields(self) -> list[str]:
        return [field.sort_by for field in self.fields if field.sortable]

    @property
    def searchable_fields(self) -> list[str]:
        return [field.search_in for field in self.fields if field.searchable]

    @property
    def searchable(self) -> bool:
        return bool(self.searchable_fields)

    @property
    def search_placeholder(self) -> str:
        template = _('Search in {fields}.')
        fields = ', '.join([field.label for field in self.fields if field.searchable])
        return template.format(fields=fields)

    def can_edit(self, request: Request) -> bool:
        return True

    def can_delete(self, request: Request) -> bool:
        return True

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        return []

    def get_route_pk_type(self) -> str:
        """
        Get route variable type.

        Used in URLs that point to a view that require object.  For example:
        /admin/users/{pk:PK_TYPE}.
        """
        raise NotImplementedError(f'{self.__class__.__name__} must implement get_pk_type() method.')

    @abc.abstractmethod
    def get_pk_value(self, entity: typing.Any) -> str:
        """Get primary key value from the entity as string."""
        raise NotImplementedError()

    @abc.abstractmethod
    def create_new_entity(self) -> typing.Any:
        """Create new entity."""
        raise NotImplementedError(f'{self.__class__.__name__} must implement create_empty_object() method.')

    @abc.abstractmethod
    async def save_entity(self, request: Request, form: wtforms.Form, instance: typing.Any) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def delete_entity(self, request: Request, instance: typing.Any) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_object(self, request: Request, pk: typing.Any) -> typing.Any | None:
        raise NotImplementedError(f'{self.__class__.__name__} must implement get_object() method.')

    @abc.abstractmethod
    async def get_objects(
        self,
        request: Request,
        state: ListState,
        filters: list[BaseFilter],
        projection: Projection | None,
    ) -> Page[typing.Any]:
        raise NotImplementedError(f'{self.__class__.__name__} must implement get_objects() method.')

    @abc.abstractmethod
    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        raise NotImplementedError()

    async def create_form_class(self, request: Request) -> typing.Type[Form]:
        return typing.cast(
            typing.Type[Form],
            type(
                f'{self.__class__.__name__}Form',
                (Form,),
                {field.name: field for field in self.get_form_fields(request)},
            ),
        )

    async def get_form_class(self, request: Request) -> typing.Type[Form]:
        """
        Get form class.

        This form class will be used as a default form for create and edit
        pages. However, if resource defines `form_class` attribute then it will
        be used.
        """
        if self.form_class:
            return self.form_class
        return await self.create_form_class(request)

    async def get_form_class_for_edit(self, request: Request) -> typing.Type[Form]:
        return await self.get_form_class(request)

    async def get_form_class_for_create(self, request: Request) -> typing.Type[Form]:
        return await self.get_form_class(request)

    def get_form_layout(self, request: Request, form: wtforms.Form, instance: typing.Any) -> LayoutComponent:
        return layout.Grid([layout.FormElement(field, max_width='lg') for field in form])

    async def validate_form(self, request: Request, form: Form, instance: typing.Any) -> bool:
        """
        Validate form.

        Use this method to apply custom form validation.
        """
        return await form.validate_async()

    async def prefill_form_choices(self, request: Request, form: Form, instance: typing.Any) -> None:
        """Use this hook to load and prefill form field choices."""
        await form.prefill(request)

    def get_default_page_actions(self, request: Request) -> typing.Iterable[Action]:
        if self.can_edit(request):
            yield LinkAction(
                icon='plus',
                color='primary',
                url=self.url_for(request, 'create'),
                label=_('Create {resource}').format(resource=self.label),
            )

    def get_page_actions(self, request: Request) -> typing.Iterable[Action]:
        return []

    def get_configured_page_actions(self, request: Request) -> typing.Iterable[Action]:
        yield from self.get_page_actions(request)
        yield from self.get_default_page_actions(request)

    def get_default_row_actions(self, request: Request) -> typing.Iterable[RowAction]:
        if self.can_edit(request):
            yield LinkRowAction(
                icon='pencil',
                url=lambda request, row_id, _: self.url_for(request, 'edit', pk=row_id),
            )
            yield LinkRowAction(
                icon='trash', color='danger', url=lambda request, row_id, _: self.url_for(request, 'delete', pk=row_id)
            )

    def get_row_actions(self, request: Request) -> typing.Iterable[RowAction]:
        return []

    def get_configured_row_actions(self, request: Request) -> typing.Iterable[RowAction]:
        yield from self.get_row_actions(request)
        yield from self.get_default_row_actions(request)

    def render_list_view(self, request: Request, page: Page) -> str:
        return self.render_table(request, page)

    def render_empty_state(self, request: Request, page_actions: list[Action]) -> str:
        return render_to_string('ohmyadmin/empty_state.html', {'request': request, 'actions': page_actions})

    def get_default_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        return []

    def get_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        return []

    def get_configured_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        yield from self.get_batch_actions(request)
        yield from self.get_default_batch_actions(request)

    def get_filters(self, request: Request) -> typing.Iterable[BaseFilter]:
        return []

    def get_metrics(self, request: Request) -> typing.Iterable[Metric]:
        return []

    def get_projections(self, request: Request) -> typing.Iterable[Projection]:
        return []

    def get_current_projection(self, request: Request) -> Projection | None:
        projection_id = request.query_params.get('_project', '')
        return {projection.slug: projection for projection in self.get_projections(request)}.get(projection_id, None)

    async def index_view(self, request: Request) -> Response:
        """Display list of objects."""
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, self.max_page_size, self.page_size)
        search_term = get_search_value(request, self.search_param)
        ordering = get_ordering_value(request, self.ordering_param)

        state = ListState(
            page=page_number,
            ordering=ordering,
            page_size=page_size,
            search_term=search_term,
            sortable_fields=self.sortable_fields,
            searchable_fields=self.searchable_fields,
        )
        page_actions = list(self.get_configured_page_actions(request))
        batch_actions = list(self.get_configured_batch_actions(request))
        metrics = list(self.get_metrics(request))

        # projections
        projection_id = request.query_params.get('_project', '')
        projections = list(self.get_projections(request))
        projection = {projection.slug: projection for projection in self.get_projections(request)}.get(
            projection_id, None
        )

        # filters
        filters = list(self.get_filters(request))
        for filter_ in filters:
            if isinstance(filter_, Prefill):
                await filter_.prefill(request, wtforms.Form())

        has_active_filters = any([filter_.is_active(request) for filter_ in filters])
        page = await self.get_objects(request, state, filters, projection)
        if not page and not has_active_filters and not search_term:
            return TemplateResponse(
                'ohmyadmin/empty_state.html',
                {
                    'page_title': self.label_plural,
                    'actions': page_actions,
                    **admin_context(request),
                },
            )

        view_content = self.render_list_view(request, page=page)
        page_actions = list(self.get_configured_page_actions(request))
        return TemplateResponse(
            self.index_template,
            {
                'objects': page,
                'resource': self,
                'request': request,
                'metrics': metrics,
                'filters': filters,
                'projection': projection,
                'projections': projections,
                'page_size': page_size,
                'pk': self.get_pk_value,
                'content': view_content,
                'page_number': page_number,
                'search_term': search_term,
                'page_actions': page_actions,
                'page_title': self.label_plural,
                'batch_actions': batch_actions,
                'search_placeholder': self.search_placeholder,
                'action_endpoint': request.url_for(self.url_name('action')),
                **admin_context(request),
            },
        )

    async def edit_view(self, request: Request) -> Response:
        """Handle object creation and editing."""
        if not self.can_edit(request):
            flash(request).error(_('You are not allowed to access this page.'))
            return RedirectResponse(url=request.url_for(self.url_name('list')), status_code=302)

        pk = request.path_params.get('pk', '')
        instance = self.create_new_entity()
        form_class = await self.get_form_class_for_create(request)
        if pk:
            instance = await self.get_object(request, pk)
            if not instance:
                raise HTTPException(404, _('Object does not exists.'))
            form_class = await self.get_form_class_for_edit(request)

        form_submitted = request.method in ['POST', 'PUT', 'PATCH', 'DELETE']
        form_data = await request.form() if form_submitted else None
        form = form_class(formdata=form_data, obj=instance)
        await self.prefill_form_choices(request, form, instance)

        if form_submitted and await self.validate_form(request, form, instance):
            assert form_data

            await form.populate_obj_async(instance)
            await self.save_entity(request, form, instance)
            flash(request).success(_('{resource} has been saved.').format(resource=self.label))
            pk = self.get_pk_value(instance)

            if '_new' in form_data:
                return RedirectResponse(url=request.url_for(self.url_name('create')), status_code=302)
            if '_edit' in form_data:
                return RedirectResponse(url=request.url_for(self.url_name('edit'), pk=pk), status_code=302)
            if '_list' in form_data:
                return RedirectResponse(url=request.url_for(self.url_name('list')), status_code=302)

        if pk:
            page_title = self.page_title_for_edit.format(entity=instance)
        else:
            page_title = self.page_title_for_create.format(resource=self.label)

        form_layout = self.get_form_layout(request, form, instance)
        return TemplateResponse(
            self.edit_template,
            {
                'form': form,
                'resource': self,
                'request': request,
                'object': instance,
                'pk': self.get_pk_value,
                'page_title': page_title,
                'form_layout': form_layout,
                'mode': 'edit' if pk else 'create',
                **admin_context(request),
            },
        )

    async def delete_view(self, request: Request) -> Response:
        """Handle object deletion."""
        pk = request.path_params['pk']
        instance = await self.get_object(request, pk)
        if not instance:
            raise HTTPException(404, _('Object does not exists.'))

        if not self.can_delete(request):
            flash(request).error(_('You are not allowed to access this page.'))
            return RedirectResponse(url=request.url_for(self.url_name('list')), status_code=302)

        if request.method == 'POST':
            await self.delete_entity(request, instance)
            flash(request).success(_('{instance} has been deleted.').format(instance=instance))
            return RedirectResponse(url=request.url_for(self.url_name('list')), status_code=302)

        return TemplateResponse(
            self.delete_template,
            {
                'request': request,
                'object': instance,
                **admin_context(request),
            },
        )

    def _get_modal_actions(self, request: Request) -> list[Dispatch]:
        actions: list[Dispatch] = []
        actions.extend([action for action in self.get_batch_actions(request) if isinstance(action, Dispatch)])
        actions.extend([action for action in self.get_page_actions(request) if isinstance(action, Dispatch)])

        for action in self.get_row_actions(request):
            if isinstance(action, ModalRowAction):
                actions.append(action.action)
            if isinstance(action, RowActionGroup):
                for subaction in action.actions:
                    if isinstance(subaction, ModalRowAction):
                        actions.append(subaction.action)

        return actions

    async def action_view(self, request: Request) -> Response:
        """Handle actions."""
        actions: dict[str, Dispatch] = {action.slug: action for action in self._get_modal_actions(request)}
        action = actions.get(request.query_params.get('_action', ''))
        if not action:
            raise HTTPException(404, 'Action does not exists.')

        return await action.dispatch(request)

    async def metric_view(self, request: Request) -> Response:
        """Handle actions."""
        metrics = {metric.slug: metric for metric in list(self.get_metrics(request))}
        metric = metrics.get(request.query_params.get('_metric', ''))
        if not metric:
            raise HTTPException(404, 'Metric does not exists.')

        return await metric.dispatch(request)

    @classmethod
    def url_name(cls, name: str = 'list') -> str:
        """Generate route name for this resource actions."""
        return f'ohmyadmin.{cls.slug}.{name}'.replace('-', '_')

    def url_for(self, request: Request, name: str, **path_params: typing.Any) -> str:
        return request.url_for(self.url_name(name), **path_params)

    def get_routes(self) -> typing.Iterable[BaseRoute]:
        pktype = self.get_route_pk_type()
        yield Route('/', self.index_view, name=self.url_name('list'))
        yield Route('/new', self.edit_view, name=self.url_name('create'), methods=['get', 'post'])
        yield Route('/edit/{pk:%s}' % pktype, self.edit_view, name=self.url_name('edit'), methods=['get', 'post'])
        yield Route('/delete/{pk:%s}' % pktype, self.delete_view, name=self.url_name('delete'), methods=['get', 'post'])
        yield Route('/action', self.action_view, name=self.url_name('action'), methods=['get', 'post'])
        yield Route('/metrics', self.metric_view, name=self.url_name('metrics'), methods=['get', 'post'])

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.setdefault('state', {})
        scope['state']['resource'] = self
        await super().__call__(scope, receive, send)
