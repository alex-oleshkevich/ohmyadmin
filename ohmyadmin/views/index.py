from starlette.requests import Request

from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.filters import Filter


class CollectionViewMixin:
    def get_datasource(self) -> DataSource:
        assert self.datasource
        return self.datasource

    def get_query_for_index(self) -> DataSource:
        return self.get_datasource().get_query_for_list()

    def get_filters(self) -> list[Filter]:
        return list(self.filters)

    async def apply_filters(self, request: Request, query: DataSource) -> DataSource:
        for filter_ in self.filters:
            filter_form = await filter_.get_form(request)
            query = filter_.apply(request, query, filter_form)
        return query
