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
from ohmyadmin.components.display import DisplayField
from ohmyadmin.components.form import Form
from ohmyadmin.flash import flash
from ohmyadmin.helpers import camel_to_sentence, pluralize, render_to_string
from ohmyadmin.i18n import _
from ohmyadmin.ordering import SortingHelper, SortingType, get_ordering_value
from ohmyadmin.pagination import Page, get_page_size_value, get_page_value
from ohmyadmin.tables import Column, get_search_value
from ohmyadmin.templating import TemplateResponse, admin_context

# class Resource2(Router):
#     def get_filters(self) -> typing.Iterable[BaseFilter]:
#         """
#         Get filters.
#
#         If resource has searchable or orderable columns then SearchFilter and
#         OrderingFilter will be added.
#         """
#
#         table_columns = list(self.get_table_columns())
#         columns = list([column for column in table_columns if column.searchable])
#         yield SearchFilter(query_param=self.search_param, entity_class=self.entity_class, columns=columns)
#
#         columns = [column for column in table_columns if column.sortable]
#         yield OrderingFilter(entity_class=self.entity_class, columns=columns, query_param=self.ordering_param)
#
#         filter_classes = self.filters or []
#         for filter_class in filter_classes:
#             yield filter_class()
#
#     async def edit_object_view(self, request: Request) -> Response:
#         file_store: FileStorage = request.state.file_storage
#         pk = request.path_params.get('pk', None)
#         session = request.state.dbsession
#         if pk:
#             instance = await self.get_object(request, pk=request.path_params['pk'])
#             if not instance:
#                 raise HTTPException(404, _('Object does not exists.'))
#         else:
#             instance = self.get_empty_object()
#
#         form_class = self.get_form_class()
#         form = await form_class.from_request(request, instance=instance)
#         layout = self.get_form_layout(request, form)
#         fields_to_exclude: list[str] = []
#         if await form.validate_on_submit(request):
#             for field in form:
#                 if isinstance(field, HandlesFiles):
#                     assert file_store, _('Cannot save uploaded file because file storage is not configured.')
#                     fields_to_exclude.append(field.name)
#                     if file_paths := await field.save(file_store, instance):
#                         entity_method_name = f'add_file_paths_for_{field.name}'
#                         entity_method = getattr(instance, entity_method_name, None)
#                         if not entity_method:
#                             raise AttributeError(
#                                 f'In order to process uploaded files, the model {instance.__class__.__name__} '
#                                 f'must define `{entity_method_name}(*file_paths: str) -> None` method. '
#                             )
#                         entity_method(*file_paths)
#
#             form.populate_obj(instance, exclude=fields_to_exclude)
#             if not pk:
#                 session.add(instance)
#             await session.commit()
#             flash(request).success(self.message_object_saved.format(label=self.label))
#             return await self._detect_post_save_action(request, instance)
#
#         object_label = str(instance) if pk else self.label
#         label_template = self.edit_page_label if pk else self.create_page_label
#
#         return render_to_response(
#             request,
#             self.edit_view_template,
#             {
#                 'form': form,
#                 'layout': layout,
#                 'request': request,
#                 'form_actions': self.get_form_actions(),
#                 'page_title': label_template.format(resource=object_label),
#             },
#         )
#
#     async def metric_view(self, request: Request) -> Response:
#         """A backend for resource metric cards."""
#         metric_id = request.path_params['metric_id']
#         metric = next((metric for metric in self.get_metrics() if metric.id == metric_id))
#         if not metric:
#             raise HTTPException(404, 'Metric does not exists.')
#         return await metric.dispatch(request)


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

        def field_link(field: Column, entity: typing.Any) -> str:
            if not field.link:
                return ''
            if field.link_factory:
                return field.link_factory(request, entity)
            return request.url_for(self.url_name('edit'), pk=self.get_pk_value(entity))

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
                'field_link': field_link,
                'row_actions': row_actions,
                'batch_actions': batch_actions,
            },
        )


class Resource(TableMixin, Router):
    icon: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    label_plural: typing.ClassVar[str] = ''
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

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        class_name = cls.__name__.removesuffix('Resource')
        cls.label = cls.label or camel_to_sentence(class_name)
        cls.label_plural = cls.label_plural or pluralize(cls.label)
        cls.slug = pluralize(slugify(camel_to_sentence(class_name)))

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
    async def get_objects(self, request: Request, state: ListState) -> Page[typing.Any]:
        raise NotImplementedError(f'{self.__class__.__name__} must implement get_objects() method.')

    @abc.abstractmethod
    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        raise NotImplementedError()

    def create_form_class(self, request: Request) -> typing.Type[Form]:
        return typing.cast(
            typing.Type[Form],
            type(
                f'{self.__class__.__name__}Form',
                (Form,),
                {field.name: field for field in self.get_form_fields(request)},
            ),
        )

    def get_form_class(self, request: Request) -> typing.Type[Form]:
        """
        Get form class.

        This form class will be used as a default form for create and edit
        pages. However, if resource defines `form_class` attribute then it will
        be used.
        """
        if self.form_class:
            return self.form_class
        return self.create_form_class(request)

    def get_form_class_for_edit(self, request: Request) -> typing.Type[Form]:
        return self.get_form_class(request)

    def get_form_class_for_create(self, request: Request) -> typing.Type[Form]:
        return self.get_form_class(request)

    async def validate_form(self, request: Request, form: Form, instance: typing.Any) -> bool:
        """
        Validate form.

        Use this method to apply custom form validation.
        """
        return await form.validate_async()

    async def prefill_form_choices(self, request: Request, form: wtforms.Form, instance: typing.Any) -> None:
        """Use this hook to load and prefill form field choices."""

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

    def get_default_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        return []

    def get_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        return []

    def get_configured_batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        yield from self.get_batch_actions(request)
        yield from self.get_default_batch_actions(request)

    async def index_view(self, request: Request) -> Response:
        """Display list of objects."""
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, self.max_page_size, self.page_size)
        search_term = get_search_value(request, self.search_param)
        ordering = get_ordering_value(request, self.ordering_param)

        state = ListState(
            page=page_number,
            page_size=page_size,
            ordering=ordering,
            search_term=search_term,
            sortable_fields=self.sortable_fields,
            searchable_fields=self.searchable_fields,
        )
        page = await self.get_objects(request, state)
        view_content = self.render_list_view(request, page=page)
        page_actions = list(self.get_configured_page_actions(request))
        batch_actions = list(self.get_configured_batch_actions(request))
        return TemplateResponse(
            self.index_template,
            {
                'objects': page,
                'resource': self,
                'request': request,
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
        form_class = self.get_form_class_for_create(request)
        if pk:
            instance = await self.get_object(request, pk)
            if not instance:
                raise HTTPException(404, _('Object does not exists.'))
            form_class = self.get_form_class_for_edit(request)

        form_data = await request.form()
        form = form_class(formdata=form_data, obj=instance)
        await self.prefill_form_choices(request, form, instance)

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if await self.validate_form(request, form, instance):
                await form.populate_obj_async(instance)
                await self.save_entity(request, form, instance)
                flash(request).success(_('{resource} has been saved.').format(resource=self.label))

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

        return TemplateResponse(
            self.edit_template,
            {
                'form': form,
                'request': request,
                'object': instance,
                'resource': self,
                'pk': self.get_pk_value,
                'page_title': page_title,
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

    @classmethod
    def url_name(cls, name: str) -> str:
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

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.setdefault('state', {})
        scope['state']['resource'] = self
        await super().__call__(scope, receive, send)
