import abc
import typing
from starlette.requests import Request

from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination

T = typing.TypeVar("T")

SearchPredicate = typing.Literal["startswith", "endswith", "exact", "matches", "like"]


class DataSource(abc.ABC, typing.Generic[T]):
    @abc.abstractmethod
    async def paginate(
        self, request: Request, page: int, page_size: int
    ) -> Pagination[T]:
        raise NotImplementedError()

    def get_query_for_list(self) -> typing.Self:
        return self

    @abc.abstractmethod
    def get_pk(self, obj: typing.Any) -> str:  # pragma: no cover
        ...

    @abc.abstractmethod
    def apply_search_filter(
        self, term: str, predicate: SearchPredicate, fields: list[str]
    ) -> typing.Self:
        raise NotImplementedError()

    @abc.abstractmethod
    def apply_ordering_filter(
        self, rules: dict[str, SortingType], fields: typing.Sequence[str]
    ) -> typing.Self:
        raise NotImplementedError()
