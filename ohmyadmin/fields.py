import sqlalchemy as sa
import typing
import wtforms

Formatter = typing.Callable[[typing.Any], str]


class Field:
    form_field_class: typing.Type[wtforms.Field] = wtforms.StringField
    cell_template = 'ohmyadmin/fields/cell_text.html'

    def __init__(
        self,
        name: str,
        *,
        title: str = '',
        description: str = '',
        sortable: bool = False,
        searchable: bool = False,
        default_value: typing.Any = None,
        source: str = '',
        search_in: str | list[str] = '',
        sort_by: str = '',
        value_format: str | Formatter = '%s',
        required: bool = True,
        placeholder: str = '',
        autocomplete: str = '',
        input_mode: str = '',
        form_kwargs: dict[str, typing.Any] | None = None,
        read_only: bool = False,
        link: bool = False,
    ) -> None:
        self.name = name
        self.title = name.replace('_', ' ').title() if title is None else title
        self.description = description
        self.sortable = sortable
        self.searchable = searchable
        self.default_value = default_value
        self.source = source or name
        self.sort_by = sort_by or self.source
        self.search_in = ([search_in] if isinstance(search_in, str) else search_in) if search_in else [self.source]
        self.value_format = value_format
        self.required = required
        self.form_placeholder = placeholder
        self.autocomplete = autocomplete
        self.input_mode = input_mode
        self.read_only = read_only
        self.link = link
        self.form_kwargs = form_kwargs or {}

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

    def create_form_field(self) -> wtforms.Field:
        validators = []
        if self.required:
            validators.append(wtforms.validators.data_required())

        widget_attrs: dict[str, str | float | bool | None] = {}
        if self.form_placeholder:
            widget_attrs['placeholder'] = self.form_placeholder
        if self.autocomplete:
            widget_attrs['autocomplete'] = self.autocomplete
        if self.input_mode:
            widget_attrs['inputmode'] = self.input_mode
        widget_attrs['readonly'] = self.read_only

        return self.form_field_class(
            label=self.title,
            description=self.description,
            default=self.default_value,
            validators=validators,
            render_kw={**widget_attrs, **self.form_kwargs},
        )


class HasFields:
    fields: typing.Sequence[Field] | None = []

    def get_fields(self) -> list[Field]:
        return list(self.fields or [])
