import dataclasses

import typing
from starlette.datastructures import URL, MultiDict
from starlette.requests import Request
from urllib.parse import parse_qsl, urlencode

SortingType = typing.Literal["asc", "desc"]


@dataclasses.dataclass
class Ordering:
    field: str
    direction: SortingType
    next_url: URL


def get_ordering_value(request: Request, param_name: str) -> dict[str, SortingType]:
    """
    Extract ordering value from query params.

    Returns a dictionary where keys are parameter names and values either 'asc' or 'desc' literals.
    """
    return {
        value[1:] if value.startswith("-") else value: "desc"
        if value.startswith("-")
        else "asc"
        for value in request.query_params.getlist(param_name)
        if value
    }


@dataclasses.dataclass
class SortControl:
    index: int | None
    url: URL
    show_index: bool
    ordering: SortingType | None


class SortingHelper:
    """API interface for managing ordering values from query parameters."""

    def __init__(self, request: Request, query_param: str) -> None:
        self.request = request
        self.query_param_name = query_param
        self.ordering = request.query_params.getlist(query_param)

    def get_current_ordering(self, field: str) -> SortingType | None:
        for order in self.ordering:
            if order == field:
                return "asc"
            if order == f"-{field}":
                return "desc"

        return None

    def get_current_ordering_index(self, field: str) -> int | None:
        for index, param_name in enumerate(self.ordering):
            if param_name.endswith(field):
                return index + 1
        return None

    def get_url(self, field: str) -> URL:
        """
        Generate a URL with inverted ordering params.

        For example, if current page has `ordering=title` then the function generates `ordering=-title`.
        """
        ordering = self.ordering.copy()
        if field in ordering:
            index = ordering.index(field)
            ordering[index] = f"-{field}"
        elif f"-{field}" in ordering:
            ordering.remove(f"-{field}")
        else:
            ordering.append(field)

        params = MultiDict(parse_qsl(self.request.url.query, keep_blank_values=True))
        params.setlist(self.query_param_name, ordering)
        url = self.request.url.replace(query=urlencode(params.multi_items()))
        return url

    def should_show_index(self) -> bool:
        """
        Test if current ordering index should be displayed next to column label.

        Typically used to highlight in what order the data source has been sorted.
        """
        return len(self.ordering) > 1

    def get_control(self, field: str) -> SortControl:
        url = self.get_url(field)
        ordering = self.get_current_ordering(field)
        index = self.get_current_ordering_index(field)
        show_index = self.should_show_index()
        return SortControl(
            index=index, ordering=ordering, url=url, show_index=show_index
        )
