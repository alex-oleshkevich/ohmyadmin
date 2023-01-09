from __future__ import annotations

import abc
import typing

from starlette.requests import Request

from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Page


class DataSource:

    @abc.abstractmethod
    def get_for_index(self) -> DataSource: ...

    def apply_search(self, search_term: str, searchable_fields: typing.Sequence[str]) -> DataSource:
        return self

    def apply_ordering(self, ordering: dict[str, SortingType], sortable_fields: typing.Sequence[str]) -> DataSource:
        return self

    def apply_filters(self, filters) -> DataSource:
        return self

    @abc.abstractmethod
    async def one(self) -> typing.Any: ...

    @abc.abstractmethod
    async def paginate(self, request: Request, page: int, page_size: int) -> Page[typing.Any]: ...
