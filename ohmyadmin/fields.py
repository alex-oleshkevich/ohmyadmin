import sqlalchemy as sa
import typing

Formatter = typing.Callable[[typing.Any], str]


class Field:
    cell_template = 'ohmyadmin/fields/cell_text.html'

    def __init__(
        self,
        name: str,
        *,
        title: str = '',
        sortable: bool = False,
        searchable: bool = False,
        source: str = '',
        search_in: str | list[str] = '',
        sort_by: str = '',
        value_format: str | Formatter = '%s',
    ) -> None:
        self.name = name
        self.title = name.replace('_', ' ').title() if title is None else title
        self.sortable = sortable
        self.searchable = searchable
        self.source = source or name
        self.sort_by = sort_by or self.source
        self.search_in = ([search_in] if isinstance(search_in, str) else search_in) if search_in else [self.source]
        self.value_format = value_format

    def get_value(self, obj: typing.Any) -> typing.Any:
        parts = self.source.split('.')
        value = obj
        for part in parts:
            value = getattr(value, part)
        return value

    def format_value(self, value: typing.Any) -> str:
        if callable(self.value_format):
            return self.value_format(value)
        return self.value_format % value

    def get_display_value(self, obj: typing.Any) -> str:
        return self.format_value(self.get_value(obj))

    def build_search_clause(self, column: sa.Column, search: str) -> sa.sql.ClauseElement:
        search_token = f'%{search.lower()}%'
        return column.ilike(search_token)


class HasFields:
    fields: typing.Sequence[Field] | None = []

    def get_fields(self) -> list[Field]:
        return list(self.fields or [])
