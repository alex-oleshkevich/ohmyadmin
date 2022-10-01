import typing
from starlette.datastructures import URL, MultiDict
from starlette.requests import Request
from urllib.parse import parse_qsl, urlencode

SortingType = typing.Literal['asc', 'desc']


def get_ordering_value(request: Request, param_name: str) -> dict[str, SortingType]:
    return {
        value[1:] if value.startswith('-') else value: 'desc' if value.startswith('-') else 'asc'
        for value in request.query_params.getlist(param_name)
        if value
    }


class SortingHelper:
    def __init__(self, request: Request, query_param: str) -> None:
        self.request = request
        self.query_param_name = query_param
        self.ordering = request.query_params.getlist(query_param)

    def get_current_ordering(self, sort_field: str) -> SortingType | None:
        for order in self.ordering:
            if order == sort_field:
                return 'asc'
            if order == f'-{sort_field}':
                return 'desc'

        return None

    def get_current_ordering_index(self, sort_field: str) -> int | None:
        for index, param_name in enumerate(self.ordering):
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
        ordering = self.ordering.copy()
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
        return len(self.ordering) > 1
