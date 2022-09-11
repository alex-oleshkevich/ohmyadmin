from __future__ import annotations

import abc
import re
import sqlalchemy as sa
import typing
from starlette.datastructures import URL, FormData, MultiDict
from starlette.requests import Request
from urllib.parse import parse_qsl, urlencode
from wtforms.fields.core import UnboundField

from ohmyadmin.actions import ActionColor
from ohmyadmin.forms import Form, FormField, Grid, Layout
from ohmyadmin.helpers import render_to_string
from ohmyadmin.responses import Response

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import PkType

Formatter = typing.Callable[[typing.Any], str]


class Column:
    name: str
    label: str
    sortable: bool = False
    searchable: bool = False
    head_template: str = 'ohmyadmin/tables/cell_head.html'
    template: str = 'ohmyadmin/tables/cell_text.html'

    def __init__(
        self,
        name: str,
        *,
        label: str = '',
        sortable: bool = False,
        searchable: bool = False,
        source: str = '',
        value_format: str | Formatter | None = None,
        sort_by: str = '',
        search_in: list[str] | None = None,
        link: bool = False,
        link_factory: typing.Callable[[Request, typing.Any], str] | None = None,
    ) -> None:
        self.name = name
        self.label = label or name.replace('_', ' ').title()
        self.sortable = sortable
        self.searchable = searchable
        self.source = source or name
        self.value_format = value_format
        self.sort_by = sort_by or self.source
        self.search_in = search_in or [self.source]
        self.link = link
        self.link_factory = link_factory

    def get_value(self, obj: typing.Any) -> typing.Any:
        parts = self.source.split('.')
        value = obj
        for part in parts:
            value = getattr(value, part)
        return value

    def format_value(self, value: typing.Any) -> str:
        if callable(self.value_format):
            return self.value_format(value)
        if self.value_format:
            return self.value_format % value
        return value

    def get_display_value(self, obj: typing.Any) -> str:
        return self.format_value(self.get_value(obj))

    def render_head_cell(self, request: Request, sorting_helper: SortingHelper) -> str:
        return render_to_string(
            self.head_template,
            {
                'column': self,
                'request': request,
                'sorting_helper': sorting_helper,
            },
        )

    def render(self, entity: typing.Any) -> str:
        return render_to_string(self.template, {'column': self, 'object': entity})

    __call__ = render


class BatchActionMeta(abc.ABCMeta):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        name = name.removesuffix('Action')
        label = re.sub(r'(?<!^)(?=[A-Z])', ' ', name).title()

        attrs['id'] = attrs.get('id', name.lower())
        attrs['label'] = attrs.get('label', label)
        return super().__new__(cls, name, bases, attrs)


class BatchAction(abc.ABC, metaclass=BatchActionMeta):
    id: str = ''
    label: str = 'Unlabelled'
    confirmation: str = ''
    dangerous: bool = False
    template: str = 'ohmyadmin/tables/batch_action.html'
    fields: typing.Iterable[UnboundField] | None = None

    @abc.abstractmethod
    async def apply(self, request: Request, ids: list[PkType], params: FormData) -> Response:
        ...

    def render(self) -> str:
        layout: Layout | None = None
        if self.fields is not None:
            form_class = Form.from_fields(self.fields)
            form = form_class()
            layout = Grid([FormField(field) for field in form], cols=1)
        return render_to_string(self.template, {'action': self, 'form': layout})

    __str__ = render


class RowAction(abc.ABC):
    template = ''

    def render(self, entity: typing.Any) -> str:
        assert self.template, 'RowAction does not define template.'
        return render_to_string(self.template, {'action': self, 'object': entity})

    __call__ = render


class LinkRowAction(RowAction):
    template = 'ohmyadmin/tables/row_action_link.html'

    def __init__(
        self,
        action_url: typing.Callable[[typing.Any], str],
        text: str = '',
        icon: str = '',
        color: ActionColor = 'default',
    ) -> None:
        self.text = text
        self.icon = icon
        self.color = color
        self.action_url = action_url

    def generate_url(self, entity: typing.Any) -> str:
        return self.action_url(entity)


class ActionGroup(RowAction):
    template = 'ohmyadmin/tables/row_action_group.html'

    def __init__(self, children: list[LinkRowAction]) -> None:
        self.children = children

    def __iter__(self) -> typing.Iterator[LinkRowAction]:
        return iter(self.children)


def get_ordering_value(request: Request, param_name: str) -> list[str]:
    return request.query_params.getlist(param_name)


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '')


def get_page_value(request: Request, param_name: str) -> int:
    page = 1
    try:
        page = max(1, int(request.query_params.get(param_name, 1)))
    except (TypeError, ValueError):
        pass
    return page


def get_page_size_value(request: Request, param_name: str, allowed: list[int], default: int) -> int:
    page_size = default
    try:
        page_size = int(request.query_params.get(param_name, default))
    except (TypeError, ValueError):
        pass
    if page_size not in allowed:
        page_size = default
    return page_size


class BaseFilter(abc.ABC):
    @abc.abstractmethod
    def apply(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        ...


class OrderingFilter(BaseFilter):
    def __init__(self, columns: list[str], query_param: str) -> None:
        self.columns = columns
        self.query_param = query_param

    def apply(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        ordering = get_ordering_value(request, self.query_param)
        if ordering:
            queryset = queryset.order_by(None)
        for order in ordering:
            field_name = order.lstrip('-')
            if field_name not in self.columns:
                continue

            queryset = queryset.order_by(sa.desc(field_name) if order.startswith('-') else field_name)
        return queryset


class SearchFilter(BaseFilter):
    def __init__(self, columns: list[str], query_param: str) -> None:
        self.columns = columns
        self.query_params = query_param

    def apply(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        clauses = []
        search_query = get_search_value(request, self.query_params)
        if not search_query:
            return queryset

        for field in self.columns:
            search_token = f'%{search_query.lower()}%'
            clauses.append(sa.column(field).ilike(search_token))

        if clauses:
            queryset = queryset.where(sa.or_(*clauses))

        return queryset


SortingType = typing.Literal['asc', 'desc']


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
