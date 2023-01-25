from __future__ import annotations

import abc
import datetime
import decimal
import enum
import typing
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination


class DataSourceError(Exception):
    """Common exception class for data source related errors."""


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


T = typing.TypeVar('T')


class DataSource(abc.ABC, typing.Generic[T]):
    @abc.abstractmethod
    def get_query_for_index(self) -> DataSource:  # pragma: no cover
        ...

    @abc.abstractmethod
    def get_pk(self, obj: typing.Any) -> str:  # pragma: no cover
        ...

    @abc.abstractmethod
    def new(self) -> typing.Any:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_search(
        self, search_term: str, searchable_fields: typing.Sequence[str]
    ) -> DataSource[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_ordering(
        self, ordering: dict[str, SortingType], sortable_fields: typing.Sequence[str]
    ) -> DataSource[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_string_filter(
        self, field: str, operation: StringOperation, value: str
    ) -> DataSource[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_number_filter(
        self, field: str, operation: NumberOperation, value: int | float | decimal.Decimal
    ) -> DataSource[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_date_filter(self, field: str, value: datetime.date) -> DataSource[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_date_range_filter(
        self, field: str, before: datetime.date | None, after: datetime.date | None
    ) -> DataSource[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_choice_filter(
        self, field: str, choices: list[typing.Any], coerce: typing.Callable
    ) -> DataSource[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_boolean_filter(self, field: str, value: bool) -> DataSource[T]:  # pragma: no cover
        pass

    @abc.abstractmethod
    async def get(self, request: Request, pk: str) -> T | None:  # pragma: no cover
        ...

    @abc.abstractmethod
    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[T]:  # pragma: no cover
        ...

    @abc.abstractmethod
    async def create(self, request: Request, model: typing.Any) -> None:  # pragma: no cover
        ...

    @abc.abstractmethod
    async def update(self, request: Request, model: typing.Any) -> None:  # pragma: no cover
        ...

    @abc.abstractmethod
    async def delete(self, request: Request, *object_ids: str) -> None:  # pragma: no cover
        ...
