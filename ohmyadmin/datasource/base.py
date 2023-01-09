from __future__ import annotations

import abc
import typing
from starlette.requests import Request

from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination


class DataSource(abc.ABC):
    @abc.abstractmethod
    def get_for_index(self) -> DataSource:
        ...

    @abc.abstractmethod
    def apply_search(self, search_term: str, searchable_fields: typing.Sequence[str]) -> DataSource:
        ...

    @abc.abstractmethod
    def apply_ordering(self, ordering: dict[str, SortingType], sortable_fields: typing.Sequence[str]) -> DataSource:
        ...

    @abc.abstractmethod
    def apply_string_filter(self, field: str, operation: str, value: str) -> DataSource:
        ...

    @abc.abstractmethod
    async def one(self) -> typing.Any:
        ...

    @abc.abstractmethod
    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[typing.Any]:
        ...
