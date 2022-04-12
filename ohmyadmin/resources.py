from __future__ import annotations

import inspect
import sqlalchemy as sa
import typing
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette.datastructures import URL, MultiDict
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Route
from urllib.parse import parse_qsl, urlencode

from ohmyadmin.choices import ChoicePopulator
from ohmyadmin.fields import Field, WithFields
from ohmyadmin.flash_messages import flash
from ohmyadmin.form_elements import FormElement, FormGroup, Section
from ohmyadmin.forms import Form
from ohmyadmin.i18n import _
from ohmyadmin.menus import MenuItem
from ohmyadmin.pagination import Page
from ohmyadmin.query import query
from ohmyadmin.validators import Validator

if typing.TYPE_CHECKING:
    from ohmyadmin.admin import OhMyAdmin
SortingType = typing.Literal['asc', 'desc']


def get_ordering_value(request: Request, param_name: str) -> list[str]:
    return request.query_params.getlist(param_name)


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '')


def get_page_value(request: Request, param_name: str) -> int:
    page = 1
    try:
        page = max(1, int(request.query_params.get(param_name, 1)))
    except TypeError:
        pass
    return page


def get_page_size_value(request: Request, param_name: str, allowed: list[int], default: int) -> int:
    page_size = default
    try:
        page_size = int(request.query_params.get(param_name, default))
    except TypeError:
        pass
    if page_size not in allowed:
        page_size = default
    return page_size


class Filter(typing.Protocol):
    def __call__(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        ...


class SortingHelper:
    def __init__(self, query_param_name: str) -> None:
        self.query_param_name = query_param_name

    def get_current_ordering(self, request: Request, sort_field: str) -> SortingType | None:
        ordering = get_ordering_value(request, self.query_param_name)
        for order in ordering:
            if order == sort_field:
                return 'asc'
            if order == f'-{sort_field}':
                return 'desc'

        return None

    def get_current_ordering_index(self, request: Request, sort_field: str) -> int | None:
        for index, param_name in enumerate(get_ordering_value(request, self.query_param_name)):
            if param_name.endswith(sort_field):
                return index + 1
        return None

    def get_next_sorting(self, current_sorting: SortingType | None) -> SortingType | None:
        match current_sorting:
            case None:
                return 'asc'
            case 'asc':
                return 'desc'
            case 'desc':
                return None

    def get_url(self, request: Request, sort_field: str) -> URL:
        ordering = get_ordering_value(request, self.query_param_name).copy()
        if sort_field in ordering:
            index = ordering.index(sort_field)
            ordering[index] = f'-{sort_field}'
        elif f'-{sort_field}' in ordering:
            ordering.remove(f'-{sort_field}')
        else:
            ordering.append(sort_field)

        params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
        params.setlist(self.query_param_name, ordering)
        url = request.url.replace(query=urlencode(params.multi_items()))
        return url

    def should_show_index(self, request: Request) -> bool:
        return len(get_ordering_value(request, self.query_param_name)) > 1


class Resource(WithFields):
    slug: str = ''
    title: str = ''
    title_plural: str = ''
    icon: str = ''
    pk_type: str = 'int'
    entity_class: typing.Any = None
    page_query_param: str = 'page'
    page_size: int = 50
    page_sizes: list[int] = [25, 50, 75, 100]
    page_size_query_param: str = 'page_size'
    ordering_query_param: str = 'ordering[]'
    search_query_param: str = 'search'
    search_placeholder: str = _('Search %(title_plural)s')
    filters: list[Filter] = []
    query_joins: list[sa.Column] = []
    query_select_related: list[sa.Column] = []
    query_prefetch_related: list[sa.Column] = []
    queryset: sa.sql.Select | None = None
    order_by: list[sa.sql.ClauseElement] | None = None
    delete_confirmation: str = _('Delete this %(title)s?')

    def __init__(self, admin: OhMyAdmin) -> None:
        if not self.title:
            self.title = self.__class__.__name__.replace('_', ' ').removesuffix('Resource').title()
        self.admin = admin
        self.title_plural = self.title_plural or self.title + 's'
        if self.page_size not in self.page_sizes:
            raise AttributeError(f'Default page size {self.page_size} is not in configured page sizes list.')

        assert self.entity_class, 'Every resource class must define "entity_class" attribute.'

    @property
    def searchable(self) -> bool:
        return any([field.searchable for field in self.get_fields()])

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route(f'/{self.slug}', self.index_view, name=self.url_name('list')),
            Route(f'/{self.slug}/create', self.create_view, methods=['get', 'post'], name=self.url_name('create')),
            Route(
                '/%(slug)s/{pk:%(pk_type)s}/edit' % {'slug': self.slug, 'pk_type': self.pk_type},
                self.update_view,
                methods=['get', 'post', 'put', 'patch'],
                name=self.url_name('edit'),
            ),
            Route(
                '/%(slug)s/{pk:%(pk_type)s}/delete' % {'slug': self.slug, 'pk_type': self.pk_type},
                self.delete_view,
                methods=['get', 'post', 'delete'],
                name=self.url_name('delete'),
            ),
        ]

    def get_menu_item(self) -> MenuItem:
        return MenuItem(label=self.title_plural, path_name=self.url_name('list'), icon=self.icon)

    def create_form_class(self, fields: list[Field]) -> typing.Type[Form]:
        form_fields = {field.name: field.create_form_field() for field in fields}
        inline_choice_populators: dict[str, ChoicePopulator] = {
            method_name: callback
            for method_name, callback in inspect.getmembers(self, inspect.ismethod)
            if method_name.startswith('choices_for_')
        }
        inline_validators: dict[str, Validator] = {
            method_name: callback
            for method_name, callback in inspect.getmembers(self, inspect.ismethod)
            if method_name.startswith('validator_for')
        }

        return typing.cast(
            typing.Type[Form],
            type(
                f'{self.slug.title()}Form',
                (Form,),
                {
                    **form_fields,
                    **inline_choice_populators,
                    **inline_validators,
                },
            ),
        )

    def get_form_class_for_creating(self) -> typing.Type[Form]:
        fields = [field for field in self.get_fields() if 'form' in field.show_on or 'create' in field.show_on]
        return self.create_form_class(fields)

    def get_form_layout_for_creating(self, form: Form) -> FormElement:
        return Section(elements=[FormGroup(self.fields_by_name[form_field.name], form_field) for form_field in form])

    def get_form_class_for_updating(self) -> typing.Type[Form]:
        fields = [field for field in self.get_fields() if 'form' in field.show_on or 'update' in field.show_on]
        return self.create_form_class(fields)

    def get_form_layout_for_updating(self, form: Form) -> FormElement:
        return self.get_form_layout_for_creating(form)

    async def index_view(self, request: Request) -> Response:
        page_number = get_page_value(request, self.page_query_param)
        page_size = get_page_size_value(request, self.page_size_query_param, self.page_sizes, self.page_size)

        queryset = self.get_queryset()
        queryset = self.filter_queryset(request, queryset)
        page = await self.paginate_query(request.state.db, queryset, page_number, page_size)

        fields = [field for field in self.get_fields() if 'index' in field.show_on]

        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_list.html',
            {
                'page': page,
                'request': request,
                'resource': self,
                'fields': fields,
                'search_value': get_search_value(request, self.search_query_param),
                'sorting_helper': SortingHelper(self.ordering_query_param),
                'edit_object_url': lambda obj: request.url_for(self.url_name('edit'), pk=obj.id),
                'create_object_url': request.url_for(self.url_name('create')),
                'delete_object_url': lambda obj: request.url_for(self.url_name('delete'), pk=obj.id),
                'search_placeholder': self.search_placeholder % {'title_plural': self.title_plural.lower()},
                'delete_confirmation': self.delete_confirmation % {'title': self.title.lower()},
            },
        )

    async def create_view(self, request: Request) -> Response:
        instance = self.entity_class()
        form_class = self.get_form_class_for_creating()
        form, data = await form_class.from_request(request)
        form_layout = self.get_form_layout_for_creating(form)

        if request.method == 'POST' and await form.validate_on_submit(request):
            form.populate_obj(instance)
            request.state.db.add(instance)
            await request.state.db.commit()
            flash(request).success(_('%(object)s has been created.') % {'object': instance})
            if '_add' in data:
                return RedirectResponse(request.url_for(self.url_name('create')), status_code=301)
            if '_return' in data:
                return RedirectResponse(request.url_for(self.url_name('list')), status_code=301)
            return RedirectResponse(request.url_for(self.url_name('edit'), pk=instance.id), status_code=301)

        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_create.html',
            {
                'form': form,
                'resource': self,
                'request': request,
                'form_layout': form_layout,
                'page_title': _('Create %(resource)s' % {'resource': self.title}),
                'list_objects_url': request.url_for(self.url_name('list')),
            },
        )

    async def update_view(self, request: Request) -> Response:
        pk = request.path_params['pk']
        stmt = self.get_queryset().where(getattr(self.entity_class, 'id') == pk)
        instance = await query(request.state.db).one_or_none(stmt)
        if not instance:
            raise HTTPException(404, _('%(title)s not found.' % {'title': self.title}))

        form_class = self.get_form_class_for_updating()
        form, data = await form_class.from_request(request, instance)
        form_layout = self.get_form_layout_for_updating(form)

        if request.method == 'POST' and await form.validate_on_submit(request):
            form.populate_obj(instance)
            await request.state.db.commit()
            flash(request).success(_('%(object)s has been updated.') % {'object': instance})
            if '_return' in data:
                return RedirectResponse(request.url_for(self.url_name('list')), status_code=301)
            return RedirectResponse(request.url_for(self.url_name('edit'), pk=instance.id), status_code=301)

        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_edit.html',
            {
                'form': form,
                'resource': self,
                'request': request,
                'object': instance,
                'form_layout': form_layout,
                'page_title': _('Edit %(object)s' % {'object': instance}),
                'list_objects_url': request.url_for(self.url_name('list')),
                'delete_object_url': lambda obj: request.url_for(self.url_name('delete'), pk=obj.id),
            },
        )

    async def delete_view(self, request: Request) -> Response:
        pk = request.path_params['pk']
        instance = await query(request.state.db).find(self.entity_class, pk)
        if not instance:
            raise HTTPException(404, _('%(title)s not found.' % {'title': self.title}))

        if request.method in ['POST', 'DELETE']:
            await request.state.db.delete(instance)
            await request.state.db.commit()
            flash(request).success(_('%(object)s has been deleted.') % {'object': instance})
            return RedirectResponse(request.url_for(self.url_name('list')), status_code=301)

        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_delete.html',
            {
                'request': request,
                'resource': self,
                'object': instance,
                'page_title': _('Delete %(object)s' % {'object': instance}),
                'list_objects_url': request.url_for(self.url_name('list')),
                'delete_confirmation': self.delete_confirmation % {'title': self.title.lower()},
            },
        )

    def url_name(self, action: str) -> str:
        return f'{self.slug}_{action}'

    def get_queryset(self) -> sa.sql.Select:
        if self.queryset is not None:
            return self.queryset

        queryset = sa.select(self.entity_class)
        if self.query_joins:
            for join in self.query_joins:
                queryset = queryset.join(join)
        queryset = queryset.options(
            *[joinedload(column) for column in self.query_select_related or []],
            *[selectinload(column) for column in self.query_prefetch_related or []],
        )

        if self.order_by:
            queryset = queryset.order_by(*self.order_by)
        return queryset

    def get_filters(self) -> list[Filter]:
        configured_filters = self.filters or []
        configured_filters.extend(
            [
                create_search_filter(self),
                create_ordering_filter(self),
            ]
        )
        return configured_filters

    def filter_queryset(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        for filter_ in self.get_filters():
            queryset = filter_(request, queryset)

        return queryset

    async def paginate_query(self, session: AsyncSession, queryset: sa.sql.Select, page: int, page_size: int) -> Page:
        return await query(session).paginate(queryset, page, page_size)


def create_search_filter(resource: Resource) -> Filter:
    searchable_fields = [field for field in resource.get_fields() if field.searchable]
    orm_columns: dict[str, list[sa.Column]] = {
        field.name: [get_column(resource.entity_class, column_name) for column_name in field.search_in]
        for field in searchable_fields
    }

    def search_filter(request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        clauses = []
        search_query = get_search_value(request, resource.search_query_param)
        if not search_query:
            return queryset
        for field in searchable_fields:
            columns = orm_columns[field.name]
            for column in columns:
                clauses.append(field.build_search_clause(column, search_query))

        if clauses:
            queryset = queryset.where(sa.or_(*clauses))

        return queryset

    return search_filter


def create_ordering_filter(resource: Resource) -> Filter:
    sortable_fields = {field.sort_by: field for field in resource.get_fields() if field.sortable}

    def ordering_filter(request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        ordering = get_ordering_value(request, resource.ordering_query_param)
        if ordering:
            queryset = queryset.order_by(None)
        for order in ordering:
            field_name = order.lstrip('-')
            if field_name not in sortable_fields:
                continue

            selectable = get_column(resource.entity_class, field_name)
            queryset = queryset.order_by(selectable.desc() if order.startswith('-') else selectable.asc())
        return queryset

    return ordering_filter


def get_column(entity_class: typing.Any, column_name: str) -> sa.Column:
    selectable = entity_class
    attribute_path = column_name.split('.')
    for attr_name in attribute_path:
        inspection = sa.inspect(selectable)
        if inspection.is_mapper:
            selectable = getattr(selectable, attr_name)
        elif inspection.is_attribute:
            if entity := getattr(inspection.comparator, 'entity'):
                selectable = getattr(entity.class_, attr_name)
            else:
                selectable = getattr(selectable, attr_name)
    return selectable
