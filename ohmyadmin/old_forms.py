from __future__ import annotations

import abc
import datetime
import decimal
import enum
import inspect
import os
import pathlib
import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import ImmutableMultiDict, UploadFile
from starlette.requests import Request
from wtforms.fields.core import UnboundField
from wtforms.form import FormMeta

from ohmyadmin.helpers import render_to_string
from ohmyadmin.storage import FileStorage

Choices = typing.Iterable[tuple[str | None, str]]
ChoicesFactory = typing.Callable[[Request, 'Form'], Choices | typing.Awaitable[Choices]]
Validator = typing.Callable[[wtforms.Field, wtforms.Field], typing.Awaitable[None] | None]

T = typing.TypeVar('T')


class Field(typing.Generic[T], wtforms.Field):
    template = 'ohmyadmin/forms/field.html'
    data: T

    def __init__(
        self,
        *,
        label: str | None = None,
        required: bool = False,
        description: str = '',
        read_only: bool = False,
        default: T | None = None,
        validators: typing.Iterable[Validator] | None = None,
        widget_attrs: dict[str, str | bool] | None = None,
        template: str | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.validators = list(validators or [])
        self.widget_attrs = widget_attrs or {}
        self.template = template or self.template

        if read_only:
            self.widget_attrs.update({'readonly': 'readonly'})

        if required:
            self.validators.append(wtforms.validators.data_required())

        super().__init__(
            label=label,
            validators=validators,
            description=description,
            default=default,
            render_kw=widget_attrs,
            **kwargs,
        )

    def render(self) -> str:
        return render_to_string(self.template, {'field': self})

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: name={self.name}>'


class CheckboxField(Field[bool], wtforms.BooleanField):
    template = 'ohmyadmin/forms/checkbox.html'


class TextField(Field[str], wtforms.StringField):
    inputmode: str = 'text'
    template = 'ohmyadmin/forms/text.html'

    def __init__(
        self,
        *,
        placeholder: str = '',
        **kwargs: typing.Any,
    ) -> None:
        widget_attrs = kwargs.pop('widget_attrs', {})
        inputmode = self.inputmode
        if inputmode:
            widget_attrs['inputmode'] = inputmode
        if placeholder:
            widget_attrs['placeholder'] = placeholder

        super().__init__(widget_attrs=widget_attrs, **kwargs)


class SlugField(TextField, wtforms.StringField):
    template = 'ohmyadmin/forms/slug.html'


class PasswordField(TextField, wtforms.PasswordField):
    template = 'ohmyadmin/forms/password.html'


class EmailField(TextField, wtforms.EmailField):
    inputmode = 'email'
    template = 'ohmyadmin/forms/email.html'


class URLField(TextField, wtforms.URLField):
    inputmode = 'url'
    template = 'ohmyadmin/forms/email.html'


class IntegerField(Field[int], wtforms.IntegerField):
    inputmode = 'numeric'
    template = 'ohmyadmin/forms/integer.html'

    def __init__(
        self,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
        step: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        validators = kwargs.pop('validators', [])
        attrs = kwargs.pop('widget_attrs', {})
        if min_value or max_value:
            validators.append(wtforms.validators.number_range(min=min_value, max=max_value))
        if step:
            attrs['step'] = step

        super().__init__(validators=validators, widget_attrs=attrs, **kwargs)


class FloatField(Field[float], wtforms.FloatField):
    inputmode = 'numeric'
    template = 'ohmyadmin/forms/float.html'
    widget = wtforms.widgets.NumberInput()

    def __init__(
        self,
        *,
        min_value: float | None = None,
        max_value: float | None = None,
        step: float | None = None,
        **kwargs: typing.Any,
    ) -> None:
        validators = kwargs.pop('validators', [])
        attrs = kwargs.pop('widget_attrs', {})
        if min_value or max_value:
            if min_value:
                attrs['min'] = min_value
            if max_value:
                attrs['max'] = max_value
            validators.append(wtforms.validators.number_range(min=min_value, max=max_value))
        if step:
            attrs['step'] = step

        super().__init__(validators=validators, widget_attrs=attrs, **kwargs)


class DecimalField(Field[decimal.Decimal], wtforms.DecimalField):
    inputmode = 'decimal'
    template = 'ohmyadmin/forms/decimal.html'


class TelField(TextField, wtforms.TelField):
    inputmode = 'tel'
    template = 'ohmyadmin/forms/tel.html'


class IntegerRangeField(Field[int], wtforms.IntegerRangeField):
    template = 'ohmyadmin/forms/integer_range.html'


class DecimalRangeField(Field[decimal.Decimal], wtforms.DecimalRangeField):
    template = 'ohmyadmin/forms/decimal_range.html'


UploadTo = typing.Callable[[UploadFile, typing.Any | None], str]


class HandlesFiles:
    name: str

    def __init__(self, upload_to: str | os.PathLike | UploadTo, **kwargs: typing.Any) -> None:
        self.upload_to = pathlib.Path(upload_to) if isinstance(upload_to, str) else upload_to
        super().__init__(**kwargs)

    async def save(self, file_storage: FileStorage, entity: typing.Any) -> list[str]:
        uploads: list[str] = []
        for upload_file in self.iter_files():
            if not upload_file.filename:
                continue

            if callable(self.upload_to):
                destination = pathlib.Path(self.upload_to(upload_file, entity))
            else:
                destination = pathlib.Path(self.upload_to) / upload_file.filename

            await file_storage.write(destination, upload_file)
            uploads.append(str(destination))
        return uploads

    @abc.abstractmethod
    def iter_files(self) -> typing.Iterable[UploadFile]:
        ...


def choices_from(
    entity_class: typing.Any,
    where: typing.Callable[[sa.sql.Select], sa.sql.Select] | None = None,
    value_column: str = 'id',
    label_column: str = 'name',
) -> ChoicesFactory:
    async def loader(request: Request, form: Form) -> Choices:
        stmt = sa.select(entity_class)
        stmt = where(stmt) if where else stmt
        return await as_choices(request.state.dbsession, stmt, label_column=label_column, value_column=value_column)

    return loader


async def as_choices(
    session: AsyncSession, stmt: sa.sql.Select, label_column: str = 'id', value_column: str = 'name'
) -> Choices:
    """Execute statement and return rows as choices suitable for use in form
    fields that require choices."""
    result = await session.scalars(stmt)
    return [(getattr(row, value_column), getattr(row, label_column)) for row in result.all()]


class HasChoices:
    choices: Choices | None

    def __init__(self, choices: Choices | ChoicesFactory | None = None, **kwargs: typing.Any) -> None:
        self._choices = choices
        super().__init__(**kwargs)

    async def get_choices(self, request: Request, form: Form) -> Choices:
        choices: Choices = []
        if self._choices is None:
            return choices

        if callable(self._choices):
            maybe_choices = self._choices(request, form)
            if inspect.iscoroutine(maybe_choices):
                choices = await maybe_choices
        else:
            choices = self._choices
        return choices


class FileField(Field[UploadFile], HandlesFiles, wtforms.FileField):
    template = 'ohmyadmin/forms/file.html'

    def iter_files(self) -> typing.Iterable[UploadFile]:
        yield self.data


class MultipleFileField(Field[list[UploadFile]], HandlesFiles, wtforms.MultipleFileField):
    template = 'ohmyadmin/forms/file_multiple.html'

    def iter_files(self) -> typing.Iterable[UploadFile]:
        yield from self.data


class HiddenField(Field[typing.Any], wtforms.HiddenField):
    template = 'ohmyadmin/forms/hidden.html'


class DateTimeField(Field[datetime.datetime], wtforms.DateTimeLocalField):
    template = 'ohmyadmin/forms/datetime.html'

    def __init__(self, *, format: list[str] | None = None, **kwargs: typing.Any) -> None:
        format = format or [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]
        super().__init__(format=format, **kwargs)


class DateField(Field[datetime.date], wtforms.DateField):
    template = 'ohmyadmin/forms/date.html'

    def __init__(self, *, format: str = "%Y-%m-%d", **kwargs: typing.Any) -> None:
        super().__init__(format=format, **kwargs)


class TimeField(Field[datetime.time], wtforms.TimeField):
    template = 'ohmyadmin/forms/time.html'


class MonthField(Field[datetime.date], wtforms.MonthField):
    template = 'ohmyadmin/forms/month.html'

    def __init__(self, *, format: str = "%Y-%m", **kwargs: typing.Any) -> None:
        super().__init__(format=format, **kwargs)


class TextareaField(Field[str], wtforms.TextAreaField):
    template = 'ohmyadmin/forms/textarea.html'

    def __init__(
        self,
        *,
        placeholder: str = '',
        min_length: int | None = None,
        max_length: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        widget_attrs = kwargs.pop('widget_attrs', {})
        if placeholder:
            widget_attrs['placeholder'] = placeholder

        validators = kwargs.pop('validators', [])
        if min_length or max_length:
            validators.append(wtforms.validators.length(min=min_length, max=max_length))

        super().__init__(validators=validators, widget_attrs=widget_attrs, **kwargs)


_SCPS = typing.ParamSpec('_SCPS')
_SCRT = typing.TypeVar('_SCRT')


def safe_coerce(callback: typing.Callable[[typing.Any], _SCRT]) -> typing.Callable[[typing.Any], _SCRT | None]:
    def coerce(value: float | typing.AnyStr) -> _SCRT | None:
        if value is None:
            return None

        try:
            return callback(value)
        except ValueError:
            return None

    return coerce


class SelectField(Field[typing.Any], HasChoices, wtforms.SelectField):
    template = 'ohmyadmin/forms/select.html'

    def __init__(
        self,
        *,
        coerce: typing.Callable = str,
        empty_choice: str | None = '',
        **kwargs: typing.Any,
    ) -> None:
        coerce = safe_coerce(coerce)
        self.empty_choice = empty_choice

        super().__init__(coerce=coerce, **kwargs)

    async def get_choices(self, request: Request, form: Form) -> Choices:
        choices = list(await super().get_choices(request, form))
        if self.empty_choice is not None:
            choices.insert(0, (None, self.empty_choice))
        return choices


class SelectMultipleField(Field[list[typing.Any]], HasChoices, wtforms.SelectMultipleField):
    template = 'ohmyadmin/forms/select_multiple.html'

    def __init__(
        self,
        *,
        coerce: typing.Callable = str,
        **kwargs: typing.Any,
    ) -> None:
        coerce = safe_coerce(coerce)

        super().__init__(coerce=coerce, **kwargs)


class RadioField(Field[typing.Any], wtforms.RadioField):
    template = 'ohmyadmin/forms/radio.html'


class FormField(Field[typing.Any], wtforms.FormField):
    def __init__(self, form_class: typing.Type[Form], **kwargs: typing.Any) -> None:
        super().__init__(form_class=form_class, **kwargs)


class ListField(Field[typing.Any], wtforms.FieldList):
    template = 'ohmyadmin/forms/list.html'

    def __init__(
        self,
        unbound_field: UnboundField,
        min_entries: int = 1,
        max_entries: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        kwargs.setdefault('default', [])
        super().__init__(unbound_field=unbound_field, min_entries=min_entries, max_entries=max_entries, **kwargs)


class MarkdownButton(enum.Enum):
    BOLD = ('bold', 'toggleBold', 'fa fa-bold', 'Bold')
    ITALIC = ('italic', 'toggleItalic', 'fa fa-italic', 'Italic')
    STRIKETHROUGH = ('strikethrough', 'toggleStrikethrough', 'fa fa-strikethrough', 'Strikethrough')

    HEADING_BIGGER = ('heading-bigger', 'toggleHeadingBigger', 'fa fa-header', 'Bigger Heading')
    HEADING_SMALLER = ('heading-smaller', 'toggleHeadingSmaller', 'fa fa-header', 'Smaller Heading')
    HEADING_1 = ('heading-1', 'toggleHeading1', 'fa fa-header header-1', 'Big Heading')
    HEADING_2 = ('heading-2', 'toggleHeading2', 'fa fa-header header-2', 'Medium Heading')
    HEADING_3 = ('heading-3', 'toggleHeading3', 'fa fa-header header-3', 'Small Heading')

    TABLE = ('table', 'drawTable', 'fa fa-table', 'Insert table')
    CODE = ('code', 'toggleCodeBlock', 'fa fa-code', 'Code')
    QUOTE = ('quote', 'toggleBlockquote', 'fa fa-quote-left', 'Quote')
    UNORDERED_LIST = ('unordered-list', 'toggleUnorderedList', 'fa fa-list-ul', 'Generic List')
    ORDERED_LIST = ('ordered-list', 'toggleOrderedList', 'fa fa-list-ol', 'Ordered List')
    LINK = ('link', 'drawLink', 'fa fa-link', 'Insert Link')
    IMAGE = ('image', 'drawImage', 'fa fa-picture-o', 'Insert image')
    HORIZONTAL_RULE = ('horizontal-rule', 'drawHorizontalRule', 'fa fa-minus', 'Insert Horizontal Line')

    PREVIEW = ('preview', 'togglePreview', 'fa fa-eye no-disable', 'Toggle preview')
    SIDE_BY_SIDE = ('side-by-side', 'toggleSideBySide', 'fa fa-columns no-disable no-mobile', 'Toggle Side-by-Side')
    FULLSCREEN = ('fullscreen', 'toggleFullScreen', 'fa fa-arrows-alt no-disable no-mobile', 'Toggle Fullscreen')

    REDO = ('redo', 'redo', 'fa fa-redo', 'Redo')
    UNDO = ('undo', 'undo', 'fa fa-undo', 'Undo')
    CLEAN_BLOCK = ('clean-block', 'cleanBlock', 'fa fa-eraser', 'Clean block')
    SEPARATOR = '|'


DEFAULT_MARKDOWN_TOOLBAR = [
    MarkdownButton.BOLD,
    MarkdownButton.ITALIC,
    MarkdownButton.SEPARATOR,
    MarkdownButton.HEADING_1,
    MarkdownButton.HEADING_2,
    MarkdownButton.HEADING_3,
    MarkdownButton.SEPARATOR,
    MarkdownButton.TABLE,
    MarkdownButton.CODE,
    MarkdownButton.QUOTE,
    MarkdownButton.UNORDERED_LIST,
    MarkdownButton.ORDERED_LIST,
    MarkdownButton.LINK,
    MarkdownButton.IMAGE,
    MarkdownButton.SEPARATOR,
    MarkdownButton.SIDE_BY_SIDE,
    MarkdownButton.FULLSCREEN,
]


class MarkdownField(Field, wtforms.TextAreaField):
    template = 'ohmyadmin/forms/markdown.html'

    def __init__(self, *, toolbar: list[MarkdownButton] | None = None, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)
        toolbar = toolbar or DEFAULT_MARKDOWN_TOOLBAR
        self.toolbar = [
            {
                'name': button.value[0],
                'action': f'EasyMDE.{button.value[1]}',
                'className': button.value[2],
                'title': button.value[3],
            }
            if button.value != '|'
            else '|'
            for button in toolbar
        ]


_E = typing.TypeVar('_E')


class Form(typing.Generic[_E], wtforms.Form):
    instance: _E | None
    __getattr__: typing.Callable[[Form, str], wtforms.Field]

    def __init__(
        self,
        formdata: ImmutableMultiDict[str, UploadFile | str] | None = None,
        obj: _E | None = None,
        prefix: str = "",
        data: dict[str, str] | None = None,
        meta: FormMeta | None = None,
        **kwargs: typing.Any,
    ):
        self.instance = obj
        super().__init__(formdata, obj, prefix, data, meta, **kwargs)

    async def validate_async(self) -> bool:
        success = True
        for name, field in self._fields.items():
            async_validators = [validator for validator in field.validators if inspect.iscoroutinefunction(validator)]
            field.validators = [validator for validator in field.validators if validator not in async_validators]
            if not field.validate(self):
                success = False

            for async_validator in async_validators:
                try:
                    await async_validator(self, field)
                except wtforms.validators.StopValidation as ex:
                    if ex.args and ex.args[0]:
                        field.errors.append(ex.args[0])
                        break
                except wtforms.ValidationError as ex:
                    success = False
                    field.errors.append(ex.args[0])

        return success

    async def validate_on_submit(self, request: Request) -> bool:
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return await self.validate_async()

        return False

    async def prefill_choices(self, request: Request) -> None:
        for field in self:
            if isinstance(field, HasChoices):
                field.choices = await field.get_choices(request, self)

            if isinstance(field, wtforms.FieldList):
                for subfield in field:
                    if isinstance(subfield, wtforms.FormField):
                        await subfield.form.prefill_choices(request)

    @classmethod
    async def from_request(
        cls,
        request: Request,
        instance: typing.Any | None = None,
        form_data: ImmutableMultiDict[str, UploadFile | str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Form:
        if form_data is None:
            form_data = await request.form() if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] else None
        form = cls(formdata=form_data, obj=instance, data=data)
        await form.prefill_choices(request)
        return form

    def populate_obj(self, obj: typing.Any, exclude: list[str] | None = None) -> None:
        exclude = exclude or []
        for name, field in self._fields.items():
            if name in exclude:
                continue
            field.populate_obj(obj, name)
