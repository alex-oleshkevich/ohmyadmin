import datetime
import decimal
import functools
import re
import typing
from starlette.requests import Request

from ohmyadmin.datasource.base import DataSource, NumberOperation, StringOperation
from ohmyadmin.ordering import SortingType
from ohmyadmin.pagination import Pagination

T = typing.TypeVar('T')


def apply_search_filter(current_obj: typing.Any, field: str, term: str) -> bool:
    field_value = getattr(current_obj, field, term).lower()
    search_term = term.lower()[1:]

    if term.startswith('^'):
        return field_value.startswith(search_term)
    if term.startswith('$'):
        return field_value.endswith(search_term)
    if term.startswith('='):
        return field_value == search_term
    if term.startswith('@'):
        return re.search(search_term, field_value) is not None
    return search_term in field_value


def search_filter(obj: typing.Any, fields: typing.Sequence[str], term: str) -> bool:
    return all([apply_search_filter(obj, field, term) for field in fields])


class InMemoryDataSource(DataSource[T]):
    def __init__(self, model_class: type[T], objects: typing.Sequence[T]) -> None:
        self.objects = list(objects)
        self.model_class = model_class
        self._generate_cache()

    def get_query_for_index(self) -> DataSource:
        return self

    def get_pk(self, obj: typing.Any) -> str:
        return str(obj.id)

    def clone(self, objects: typing.Sequence[T] | None = None) -> DataSource[T]:
        return InMemoryDataSource(
            model_class=self.model_class,
            objects=self.objects if objects is None else objects,
        )

    def apply_search(self, search_term: str, searchable_fields: typing.Sequence[str]) -> DataSource[T]:
        filtered = [obj for obj in self.objects if search_filter(obj, searchable_fields, search_term)]
        return self.clone(objects=filtered)

    def apply_ordering(self, ordering: dict[str, SortingType], sortable_fields: typing.Sequence[str]) -> DataSource[T]:
        def get_key(obj: typing.Any, field: str) -> str:
            return getattr(obj, field)

        filtered = self.objects.copy()
        for field, direction in ordering.items():
            if field not in sortable_fields:
                continue
            filtered = sorted(self.objects, key=functools.partial(get_key, field=field), reverse=direction == 'desc')
        return self.clone(objects=filtered)

    def apply_string_filter(self, field: str, operation: StringOperation, value: str) -> DataSource[T]:
        value = value.lower()

        def get_value(obj: typing.Any, attr: str) -> str:
            return getattr(obj, attr, '').lower()

        assert operation in StringOperation
        match operation:
            case StringOperation.startswith:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field).startswith(value)])
            case StringOperation.endswith:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field).endswith(value)])
            case StringOperation.contains:
                return self.clone(objects=[obj for obj in self.objects if value in get_value(obj, field)])
            case StringOperation.pattern:
                return self.clone(objects=[obj for obj in self.objects if re.match(value, get_value(obj, field))])
            case StringOperation.exact:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field) == value])

    def apply_number_filter(
        self, field: str, operation: NumberOperation, value: int | float | decimal.Decimal
    ) -> DataSource[T]:
        def get_value(obj: typing.Any, attr: str) -> int | float | decimal.Decimal:
            return getattr(obj, attr, 0)

        assert operation in NumberOperation
        match operation:
            case NumberOperation.eq:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field) == value])
            case NumberOperation.gt:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field) > value])
            case NumberOperation.gte:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field) >= value])
            case NumberOperation.lt:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field) < value])
            case NumberOperation.lte:
                return self.clone(objects=[obj for obj in self.objects if get_value(obj, field) <= value])

    def apply_date_filter(self, field: str, value: datetime.date | datetime.datetime) -> DataSource[T]:
        return self.clone(objects=[obj for obj in self.objects if getattr(obj, field, None) == value])

    def apply_date_range_filter(
        self,
        field: str,
        before: datetime.date | datetime.datetime | None,
        after: datetime.date | datetime.datetime | None,
    ) -> DataSource[T]:
        def check_before(obj: typing.Any) -> bool:
            value = getattr(obj, field, None)
            if value is None:
                return False
            return value <= before

        def check_after(obj: typing.Any) -> bool:
            value = getattr(obj, field, None)
            if value is None:
                return False
            return value >= after

        return self.clone(
            objects=[
                obj
                for obj in self.objects
                if all(
                    [
                        check_before(obj) if before else True,
                        check_after(obj) if after else True,
                    ]
                )
            ]
        )

    def apply_choice_filter(self, field: str, choices: list[typing.Any], coerce: typing.Callable) -> DataSource[T]:
        def get_value(obj: typing.Any, attr: str) -> typing.Any:
            return coerce(getattr(obj, attr, ''))

        return self.clone(objects=[obj for obj in self.objects if get_value(obj, field) in choices])

    def apply_boolean_filter(self, field: str, value: bool) -> DataSource[T]:
        return self.clone(objects=[obj for obj in self.objects if getattr(obj, field) is value])

    async def get(self, request: Request, pk: str) -> T | None:
        return self._by_pk.get(pk)

    async def paginate(self, request: Request, page: int, page_size: int) -> Pagination[T]:
        start_offset = max(0, page - 1) * page_size
        end_offset = start_offset + page_size
        result = self.objects[start_offset:end_offset]
        return Pagination(rows=result, total_rows=len(self.objects), page=page, page_size=page_size)

    async def create(self, request: Request, model: typing.Any) -> None:
        self.objects.append(model)
        self._generate_cache()

    async def delete(self, request: Request, *object_ids: str) -> None:
        for object_id in object_ids:
            self.objects.remove(self._by_pk[object_id])
        self._generate_cache()

    def new(self) -> typing.Any:
        return self.model_class()

    async def update(self, request: Request, model: typing.Any) -> None:
        pass

    def _generate_cache(self) -> None:
        self._by_pk: dict[str, T] = {self.get_pk(obj): obj for obj in self.objects}
