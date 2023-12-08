import abc

from starlette.requests import Request

from ohmyadmin.datasources import datasource
from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.ordering import get_ordering_value


class Filter(abc.ABC):
    visible = True

    def apply(self, request: Request, query: DataSource) -> DataSource:
        return query


class SearchFilter(Filter):
    visible = False

    def __init__(self, search_param: str, searchable_fields: list[str]) -> None:
        self.search_param = search_param
        self.searchable_fields = searchable_fields

    def apply(self, request: Request, query: DataSource) -> DataSource:
        value = request.query_params.get(self.search_param, "")
        if not value:
            return query

        if value.startswith("^"):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.STARTSWITH,
                            case_insensitive=True,
                        )
                        for field in self.searchable_fields
                    ]
                )
            )
        if value.startswith("="):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.EXACT,
                            case_insensitive=True,
                        )
                        for field in self.searchable_fields
                    ]
                )
            )
        if value.startswith("$"):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.ENDSWITH,
                            case_insensitive=True,
                        )
                        for field in self.searchable_fields
                    ]
                )
            )
        if value.startswith("@"):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.MATCHES,
                            case_insensitive=True,
                        )
                        for field in self.searchable_fields
                    ]
                )
            )

        return query.filter(
            datasource.OrFilter(
                [
                    datasource.StringFilter(
                        field=field, value=value, predicate=datasource.StringOperation.CONTAINS, case_insensitive=True
                    )
                    for field in self.searchable_fields
                ]
            )
        )


class OrderingFilter(Filter):
    def __init__(self, ordering_param: str, orderable_fields: list[str]) -> None:
        self.ordering_param = ordering_param
        self.orderable_fields = orderable_fields

    def apply(self, request: Request, query: DataSource) -> DataSource:
        ordering = get_ordering_value(request, self.ordering_param)
        return query.order_by({k: v for k, v in ordering.items() if k in self.orderable_fields})
