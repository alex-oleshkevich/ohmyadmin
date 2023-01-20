import datetime
import decimal
import typing
from starlette.requests import Request

from ohmyadmin.datasource.base import DataSource, NumberOperation, StringOperation
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination


class InMemoryDataSource(DataSource):
    def __init__(self, objects: typing.Sequence[typing.Any]) -> None:
        self.objects = objects

    def get_query_for_index(self) -> DataSource:
        return self

    def get_pk(self, obj: typing.Any) -> str:
        return obj.id

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

    async def get(self, request: Request, pk: str) -> typing.Any:
        return self.objects[0]

    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[typing.Any]:
        return Pagination(rows=self.objects, total_rows=len(self.objects), page=page, page_size=page_size)

    async def create(self, request: Request, model: typing.Any) -> typing.Any:
        return None

    async def delete(self, request: Request, *object_ids: str) -> None:
        pass

    def new(self) -> typing.Any:
        pass

    async def update(self, request: Request, model: typing.Any) -> None:
        pass
