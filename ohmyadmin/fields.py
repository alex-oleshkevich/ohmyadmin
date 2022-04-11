import sqlalchemy as sa
import typing
import wtforms

from ohmyadmin.validators import Validator

Formatter = typing.Callable[[typing.Any], str]

ShowOnType = typing.Literal['index', 'form', 'create', 'update']


class Field:
    form_field_class: typing.Type[wtforms.Field] = wtforms.StringField
    cell_template = 'ohmyadmin/fields/cell_text.html'
    form_field_template = 'ohmyadmin/fields/form_text.html'

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
        form_placeholder: str = '',
        form_autocomplete: str = '',
        form_input_mode: str = '',
        form_kwargs: dict[str, typing.Any] | None = None,
        read_only: bool = False,
        link: bool = False,
        validators: list[Validator] | None = None,
        show_on: list[ShowOnType] | None = None,
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
        self.read_only = read_only
        self.link = link
        self.show_on = list(show_on or ['index', 'form'])
        self.validators = validators or []
        self.form_kwargs = form_kwargs or {}

        if form_autocomplete:
            self.form_kwargs['autocomplete'] = form_autocomplete
        if form_placeholder:
            self.form_kwargs['placeholder'] = form_placeholder
        if form_input_mode:
            self.form_kwargs['inputmode'] = form_input_mode
        if read_only:
            self.form_kwargs['readonly'] = True

        assert self.show_on

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

    def get_form_field_args(self) -> dict[str, typing.Any]:
        return {}

    def create_form_field(self) -> wtforms.Field:
        return self.form_field_class(
            label=self.title,
            description=self.description,
            default=self.default_value,
            validators=self.get_validators(),
            render_kw=self.form_kwargs,
            **self.get_form_field_args(),
        )

    def get_validators(self) -> list[Validator]:
        validators = self.validators.copy()
        if self.required:
            validators.append(wtforms.validators.data_required())
        return validators


class SelectField(Field):
    form_field_class: typing.Type[wtforms.Field] = wtforms.SelectField
    form_field_template = 'ohmyadmin/fields/form_select.html'
    coerce: typing.Callable[[typing.Any], typing.Any] = str

    def __init__(self, *args: typing.Any, choices: list[tuple[str, str]] | None = None, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices or []

    def get_form_field_args(self) -> dict[str, typing.Any]:
        return {'coerce': self.coerce, 'choices': self.choices}


class IntegerSelectField(SelectField):
    coerce = int


class TextareaField(Field):
    form_field_class: typing.Type[wtforms.Field] = wtforms.TextAreaField
    form_field_template = 'ohmyadmin/fields/form_textarea.html'


class CheckboxField(Field):
    form_field_class: typing.Type[wtforms.Field] = wtforms.BooleanField
    form_field_template = 'ohmyadmin/fields/form_checkbox.html'


class WithFields:
    fields: typing.Sequence[Field] | None = []

    @property
    def fields_by_name(self) -> dict[str, Field]:
        return {field.name: field for field in self.get_fields()}

    def get_fields(self) -> list[Field]:
        return list(self.fields or [])
