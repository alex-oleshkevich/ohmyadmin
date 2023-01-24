import abc
import datetime
import decimal
import functools
import typing
from starlette.requests import Request

from ohmyadmin.datasource.base import DataSource, DoesNotExists, NumberOperation, StringOperation
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination

T = typing.TypeVar('T')


class InMemoryDataSource(DataSource[T]):
    def __init__(self, model_class: type[T], objects: typing.Sequence[T]) -> None:
        self.objects = list(objects)
        self._filters: list = []
        self._ordering = {}
        self.model_class = model_class
        self._by_pk: dict[str, T] = {self.get_pk(obj): obj for obj in self.objects}

    def get_query_for_index(self) -> DataSource:
        return self

    def get_pk(self, obj: typing.Any) -> str:
        return str(obj.id)

    def apply_search(self, search_term: str, searchable_fields: typing.Sequence[str]) -> DataSource:
        return self

    def apply_ordering(self, ordering: dict[str, SortingType], sortable_fields: typing.Sequence[str]) -> DataSource:
        return self

    def apply_string_filter(self, field: str, operation: StringOperation, value: str) -> DataSource:
        return self

    def apply_number_filter(
        self, field: str, operation: NumberOperation, value: int | float | decimal.Decimal
    ) -> DataSource:
        return self

    def apply_date_filter(self, field: str, value: datetime.date) -> DataSource:
        return self

    def apply_date_range_filter(
        self, field: str, before: datetime.date | None, after: datetime.date | None
    ) -> DataSource:
        return self

    def apply_choice_filter(self, field: str, choices: list[typing.Any], coerce: typing.Callable) -> DataSource:
        return self

    def apply_boolean_filter(self, field: str, value: bool) -> DataSource:
        return self

    async def get(self, request: Request, pk: str) -> T:
        try:
            return self._by_pk[pk]
        except KeyError:
            raise DoesNotExists(f'Object pk={pk} does not exists.')

    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[typing.Any]:
        start_offset = min(0, page - 1) * page_size
        end_offset = start_offset + page_size
        result = self.objects[start_offset:end_offset]
        return Pagination(rows=result, total_rows=len(self.objects), page=page, page_size=page_size)

    async def create(self, request: Request, model: typing.Any) -> typing.Any:
        return self.objects.append(model)

    async def delete(self, request: Request, *object_ids: str) -> None:
        for object_id in object_ids:
            self.objects.remove(self._by_pk[object_id])

    def new(self) -> typing.Any:
        return self.model_class()

    async def update(self, request: Request, model: typing.Any) -> None:
        pass
