from __future__ import annotations

import abc
import decimal
import enum
import typing
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination


class StringOperation(enum.Enum):
    exact = _('same as', domain='ohmyadmin')
    startswith = _('starts with', domain='ohmyadmin')
    endswith = _('ends with', domain='ohmyadmin')
    contains = _('contains', domain='ohmyadmin')
    pattern = _('matches', domain='ohmyadmin')

    @classmethod
    def choices(cls) -> typing.Sequence[tuple[str, str]]:
        return [(choice.name, choice.value) for choice in cls]


class NumberOperation(enum.Enum):
    eq = _('equals', domain='ohmyadmin')
    gt = _('is greater than', domain='ohmyadmin')
    gte = _('is greater than or equal', domain='ohmyadmin')
    lt = _('is less than', domain='ohmyadmin')
    lte = _('is less than or equal', domain='ohmyadmin')

    @classmethod
    def choices(cls) -> typing.Sequence[tuple[str, str]]:
        return [(choice.name, choice.value) for choice in cls]


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
    def apply_string_filter(self, field: str, operation: StringOperation, value: str) -> DataSource:
        ...

    @abc.abstractmethod
    def apply_number_filter(
        self, field: str, operation: NumberOperation, value: int | float | decimal.Decimal
    ) -> DataSource:
        ...

    @abc.abstractmethod
    async def one(self) -> typing.Any:
        ...

    @abc.abstractmethod
    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[typing.Any]:
        ...
