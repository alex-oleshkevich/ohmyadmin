import sqlalchemy as sa
import typing
from sqlalchemy.orm import InstrumentedAttribute
from starlette.datastructures import URL, MultiDict
from starlette.requests import Request
from urllib.parse import parse_qsl, urlencode

SortingType = typing.Literal['asc', 'desc']


def get_ordering_value(request: Request, param_name: str) -> list[str]:
    return request.query_params.getlist(param_name)


def apply_ordering(
    request: Request,
    columns: list[InstrumentedAttribute],
    stmt: sa.sql.Select,
    query_param: str = 'ordering',
) -> sa.sql.Select:
    ordering = get_ordering_value(request, query_param)
    if ordering:
        stmt = stmt.order_by(None)

    columns_by_name = {column.key: column for column in columns}
    for order in ordering:
        field_name = order.lstrip('-')
        if field_name not in columns_by_name:
            continue

        column = columns_by_name[field_name]
        stmt = stmt.order_by(sa.desc(column) if order.startswith('-') else column)
    return stmt


class SortingHelper:
    def __init__(self, request: Request, query_param_name: str) -> None:
        self.request = request
        self.query_param_name = query_param_name

    def get_current_ordering(self, sort_field: str) -> SortingType | None:
        ordering = get_ordering_value(self.request, self.query_param_name)
        for order in ordering:
            if order == sort_field:
                return 'asc'
            if order == f'-{sort_field}':
                return 'desc'

        return None

    def get_current_ordering_index(self, sort_field: str) -> int | None:
        for index, param_name in enumerate(get_ordering_value(self.request, self.query_param_name)):
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

    def get_url(self, sort_field: str) -> URL:
        ordering = get_ordering_value(self.request, self.query_param_name).copy()
        if sort_field in ordering:
            index = ordering.index(sort_field)
            ordering[index] = f'-{sort_field}'
        elif f'-{sort_field}' in ordering:
            ordering.remove(f'-{sort_field}')
        else:
            ordering.append(sort_field)

        params = MultiDict(parse_qsl(self.request.url.query, keep_blank_values=True))
        params.setlist(self.query_param_name, ordering)
        url = self.request.url.replace(query=urlencode(params.multi_items()))
        return url

    def should_show_index(self, request: Request) -> bool:
        return len(get_ordering_value(request, self.query_param_name)) > 1
