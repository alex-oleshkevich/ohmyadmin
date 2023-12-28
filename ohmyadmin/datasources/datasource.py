from __future__ import annotations

import abc
import dataclasses
import datetime
import decimal
import enum
import typing

from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination

T = typing.TypeVar("T")

SearchPredicate = typing.Literal["startswith", "endswith", "exact", "matches", "like"]


class DataSourceError(Exception):
    ...


class DuplicateError(DataSourceError):
    """Should be raised when datasource tries to insert a duplicate resource."""


class NoObjectError(DataSourceError):
    """Should be raised when datasource returned zero values but at least one expected."""


class StringOperation(enum.Enum):
    CONTAINS = _("contains", domain="ohmyadmin")
    STARTSWITH = _("starts with", domain="ohmyadmin")
    ENDSWITH = _("ends with", domain="ohmyadmin")
    EXACT = _("same as", domain="ohmyadmin")
    MATCHES = _("matches", domain="ohmyadmin")

    @classmethod
    def choices(cls) -> typing.Sequence[tuple[str, str]]:
        return [(choice.name, choice.value) for choice in cls]


class NumberOperation(enum.Enum):
    EQUALS = _("equals", domain="ohmyadmin")
    GREATER = _("is greater than", domain="ohmyadmin")
    GREATER_OR_EQUAL = _("is greater than or equal", domain="ohmyadmin")
    LESS = _("is less than", domain="ohmyadmin")
    LESS_OR_EQUAL = _("is less than or equal", domain="ohmyadmin")

    @classmethod
    def choices(cls) -> typing.Sequence[tuple[str, str]]:
        return [(choice.name, choice.value) for choice in cls]


class DateOperation(enum.Enum):
    EQUALS = _("equals", domain="ohmyadmin")
    AFTER = _("after", domain="ohmyadmin")
    BEFORE = _("before", domain="ohmyadmin")

    @classmethod
    def choices(cls) -> typing.Sequence[tuple[str, str]]:
        return [(choice.name, choice.value) for choice in cls]


@dataclasses.dataclass
class StringFilter:
    field: str
    value: str
    predicate: StringOperation
    case_insensitive: bool = False


@dataclasses.dataclass
class NumberFilter:
    field: str
    value: int | float | decimal.Decimal
    predicate: NumberOperation


@dataclasses.dataclass
class DateFilter:
    field: str
    value: datetime.date | datetime.datetime
    predicate: DateOperation


@dataclasses.dataclass
class DateTimeFilter:
    field: str
    value: datetime.date | datetime.datetime
    predicate: DateOperation


@dataclasses.dataclass
class DateRangeFilter:
    field: str
    from_value: datetime.date | datetime.datetime | None = None
    to_value: datetime.date | datetime.datetime | None = None


@dataclasses.dataclass
class DateTimeRangeFilter:
    field: str
    from_value: datetime.date | datetime.datetime | None = None
    to_value: datetime.date | datetime.datetime | None = None


@dataclasses.dataclass
class InFilter:
    field: str
    values: typing.Sequence[typing.Any]


@dataclasses.dataclass
class OrFilter:
    filters: typing.Sequence[QueryFilter] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class AndFilter:
    filters: typing.Sequence[QueryFilter] = dataclasses.field(default_factory=list)


ValueFilter: typing.TypeAlias = (
    StringFilter | NumberFilter | DateFilter | DateTimeFilter | DateRangeFilter | DateTimeRangeFilter | InFilter
)
QueryFilter: typing.TypeAlias = OrFilter | AndFilter | ValueFilter


class DataSource(abc.ABC, typing.Generic[T]):
    @abc.abstractmethod
    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[T]:
        raise NotImplementedError()

    @abc.abstractmethod
    async def count(self, request: Request) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    async def one(self, request: Request) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def update(self, request: Request, instance: T) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def create(self, request: Request, instance: T) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def delete(self, request: Request, instance: T) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def delete_all(self, request: Request) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def new(self) -> T:
        raise NotImplementedError()

    def get_query_for_list(self) -> typing.Self:
        return self

    @abc.abstractmethod
    def get_pk(self, obj: typing.Any) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def order_by(self, sorting: typing.Mapping[str, SortingType]) -> typing.Self:
        raise NotImplementedError()

    @abc.abstractmethod
    def filter(self, clause: QueryFilter) -> typing.Self:
        raise NotImplementedError()

    def get_id_field(self) -> str:
        return "id"
