from __future__ import annotations

import abc
import datetime
import inspect
import itertools
import os.path
import random
import string
import time
import typing
import wtforms
from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request
from wtforms.utils import unset_value

from ohmyadmin.storage import FileStorage
from ohmyadmin.templating import macro

UploadFilename = typing.Callable[[UploadFile, typing.Any], str]
Validator = typing.Callable[[wtforms.Form, wtforms.Field], None]
Choices = typing.Iterable[tuple[str | None, str]]
ChoicesFactory = typing.Callable[[Request, 'Form'], typing.Awaitable[Choices]]

StringField = wtforms.StringField
BooleanField = wtforms.BooleanField
TextAreaField = wtforms.TextAreaField
MonthField = wtforms.MonthField
DateField = wtforms.DateField
TimeField = wtforms.TimeField
DateTimeField = wtforms.DateTimeField
HiddenField = wtforms.HiddenField
PasswordField = wtforms.PasswordField
TelField = wtforms.TelField
URLField = wtforms.URLField
EmailField = wtforms.EmailField
FloatField = wtforms.FloatField
IntegerField = wtforms.IntegerField
DecimalField = wtforms.DecimalField
IntegerRangeField = wtforms.IntegerRangeField
DecimalRangeField = wtforms.DecimalRangeField


class Prefill(abc.ABC):
    @abc.abstractmethod
    async def prefill(self, request: Request, form: Form) -> None:
        ...


class Uploader:
    def __init__(self, storage: FileStorage, upload_to: str | UploadFilename) -> None:
        self.storage = storage
        self.destination = upload_to

    def get_format_tokens(self, upload_file: UploadFile, entity: typing.Any) -> dict[str, typing.Any]:
        prefix = ''.join(random.choices(string.ascii_lowercase, k=6))
        file_name, ext = os.path.splitext(upload_file.filename)
        timestamp = int(time.time())
        current_date = datetime.datetime.now().date().isoformat()
        current_time = datetime.datetime.now().time().isoformat()
        ext = ext[1:]

        # try to infer entity primary key
        pk = ''
        if hasattr(entity, 'get_pk'):
            pk = entity.get_pk()
        elif hasattr(entity, 'id'):
            pk = str(entity.slug)

        return {
            'prefix': prefix,
            'ext': ext,
            'name': file_name,
            'timestamp': timestamp,
            'date': current_date,
            'time': current_time,
            'file_name': upload_file.filename,
            'pk': pk,
        }

    def generate_filename(self, entity: typing.Any, upload_file: UploadFile) -> str:
        destination = self.destination if isinstance(self.destination, str) else self.destination(upload_file, entity)
        format_tokens = self.get_format_tokens(upload_file, entity)
        if '{pk}' in destination and not format_tokens['pk']:
            raise AttributeError(
                f'Uploader {self.__class__.__name__} requires {{pk}} format token in the generated file path '
                f'but entity class {entity.__class__.__name__} '
                f'does not define `get_pk() -> str` method or `id` property. '
                f'Please, define the method or property first, or override `get_format_tokens` method of this uploader.'
            )

        return destination.format(**format_tokens)

    async def upload(self, upload_file: UploadFile, path: str) -> str:
        return await self.storage.write(path, upload_file)

    def parse_entity_value(self, value: typing.Any) -> typing.Any:
        return value

    def set_file(self, entity: typing.Any, attr: str, filename: str) -> None:
        setattr(entity, attr, filename)

    async def delete_file(self, entity: typing.Any, attr: str, filename: typing.Any) -> None:
        await self.storage.delete(filename)
        setattr(entity, attr, None)


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


def coerce_bool(value: str) -> bool:
    return value in ['1', 1, True, 'true', 'True', 'on']


class TrixField(wtforms.TextAreaField):
    widget = macro('ohmyadmin/forms.html', 'trix_input')


class RichTextField(wtforms.TextAreaField):
    ...


class MarkdownField(wtforms.TextAreaField):
    ...


class SlugField(wtforms.StringField):
    ...


class FileField(wtforms.FileField):
    data: UploadFile | None

    def __init__(
        self,
        *,
        uploader: Uploader,
        label: str | None = None,
        validators: typing.Callable[[wtforms.Form, wtforms.Field], None] | None = None,
        description: str = "",
        id: str | None = None,
        render_kw: dict[str, typing.Any] | None = None,
        name: str | None = None,
        **kwargs: typing.Any,
    ):
        super().__init__(
            label,
            validators=validators,
            description=description,
            id=id,
            render_kw=render_kw,
            name=name,
            **kwargs,
        )
        self.uploader = uploader
        self._should_delete = False

    def process(
        self, formdata: FormData, data: str = unset_value, extra_filters: typing.Callable | None = None
    ) -> None:
        if formdata:
            marker = '%s-delete' % self.name
            if marker in formdata:
                self._should_delete = True

        super().process(formdata, data, extra_filters)  # noqa

    def process_data(self, value: typing.Any) -> None:
        self.data = self.uploader.parse_entity_value(value)

    def process_formdata(self, valuelist: list) -> None:
        if self._should_delete:
            self.data = None
        elif valuelist:
            for data in valuelist:
                if self._is_uploaded_file(data):
                    self.data = data
                    break

    def populate_obj(self, obj: typing.Any, name: str) -> None:
        raise RuntimeError(
            f'{self.__class__.__name__}.populate_obj cannot be used in async environment. '
            'Use populate_obj_async instead.'
        )

    async def populate_obj_async(self, entity: typing.Any, name: str) -> None:
        current_value = getattr(entity, name, None)
        if current_value and self._should_delete:
            await self.uploader.delete_file(entity, name, current_value)
            return

        if self._is_uploaded_file(self.data):
            if current_value:
                await self.uploader.delete_file(entity, name, current_value)

            assert self.data
            filename = self.uploader.generate_filename(entity, self.data)
            filename = await self.uploader.upload(self.data, filename)
            self.data.filename = filename
            self.uploader.set_file(entity, name, filename)

    def _is_uploaded_file(self, value: UploadFile | None) -> bool:
        return bool(value and isinstance(value, UploadFile) and value.filename)


class ImageField(wtforms.FileField):
    ...


class DropZoneField(wtforms.FileField):
    ...


class SelectField(wtforms.SelectField, Prefill):
    def __init__(
        self,
        label: str | None = None,
        validators: list[Validator] | None = None,
        coerce: typing.Callable = str,
        choices: Choices | ChoicesFactory | None = None,
        validate_choice: bool = True,
        **kwargs: typing.Any,
    ):
        self._async_choices: ChoicesFactory | None = None
        if callable(choices) and inspect.iscoroutinefunction(choices):
            self._async_choices = choices
            choices = None
        super().__init__(label, validators, coerce, choices=choices, validate_choice=validate_choice, **kwargs)

    async def prefill(self, request: Request, form: Form) -> None:
        if self._async_choices:
            self.choices = await self._async_choices(request, form)


class RadioField(wtforms.RadioField):
    ...


class ListWidget:
    def __call__(self, field: wtforms.Field, **kwargs: typing.Any) -> str:
        macros = macro('ohmyadmin/forms.html', 'list_field')
        return macros(field)


class GridWidget:
    def __init__(self, columns: int = 1, gap: int = 5) -> None:
        self.columns = columns
        self.gap = gap

    def __call__(self, field: wtforms.Field, **kwargs: typing.Any) -> str:
        macros = macro('ohmyadmin/forms.html', 'grid_layout')
        return macros(field, self)


class FieldList(wtforms.FieldList, Prefill):
    widget = ListWidget()

    @property
    def empty(self) -> wtforms.Field:
        field = self.append_entry()
        self.pop_entry()
        index = str(self.last_index + 1)

        if isinstance(field, wtforms.FormField):
            for subfield in field:
                subfield.render_kw = {
                    **(field.render_kw or {}),
                    'x-bind:id': '`%s`' % subfield.id.replace(index, '${index}'),
                    'x-bind:name': '`%s`' % subfield.name.replace(index, '${index}'),
                }
        else:
            field.render_kw = {
                **(field.render_kw or {}),
                'x-bind:id': '`%s`' % field.id.replace(index, '${index}'),
                'x-bind:name': '`%s`' % field.name.replace(index, '${index}'),
            }
        return field

    async def populate_obj_async(self, obj: typing.Any, name: str) -> None:
        values = getattr(obj, name, None)
        try:
            ivalues = iter(values)  # type: ignore[arg-type]
        except TypeError:
            ivalues = iter([])

        candidates = itertools.chain(ivalues, itertools.repeat(None))
        _fake = type("_fake", (object,), {})
        output = []
        for field, data in zip(self.entries, candidates):
            fake_obj = _fake()
            fake_obj.data = data
            if hasattr(field, 'populate_obj_async'):
                await field.populate_obj_async(fake_obj, 'data')
            else:
                field.populate_obj(fake_obj, "data")
            output.append(fake_obj.data)

        setattr(obj, name, output)

    async def prefill(self, request: Request, form: Form) -> None:
        for field in self.entries:
            if isinstance(field, Prefill):
                await field.prefill(request, form)


class FormField(wtforms.FormField, Prefill):
    async def prefill(self, request: Request, form: Form) -> None:
        for field in self.form:
            if isinstance(field, Prefill):
                await field.prefill(request, self.form)

    async def populate_obj_async(self, obj: typing.Any, name: str) -> None:
        candidate = getattr(obj, name, None)
        if candidate is None:
            if self._obj is None:
                raise TypeError(
                    "populate_obj: cannot find a value to populate from" " the provided obj or input data/defaults"
                )
            candidate = self._obj

        if hasattr(self.form, 'populate_obj_async'):
            await self.form.populate_obj_async(candidate)
        else:
            self.form.populate_obj(candidate)
        setattr(obj, name, candidate)


class JSONField(wtforms.TextAreaField):
    ...


class CodeField(wtforms.TextAreaField):
    ...


class CheckboxListWidget:
    def __call__(self, field: wtforms.Field, **kwargs: typing.Any) -> str:
        kwargs.setdefault("id", field.id)
        html: list[str] = []
        for subfield in field:
            html.append('<div class="form-check mb-1">')
            html.append(f'{subfield} <label for="{subfield.id}">{subfield.label.text}</label>')
            html.append('</div>')
        return ''.join(html)


class Form(wtforms.Form):
    __getattr__: typing.Callable[[wtforms.Form, str], wtforms.Field]

    async def populate_obj_async(self, obj: typing.Any) -> None:
        """
        Async version of wtforms.Form.populate_obj.

        Mostly required to handle file uploads.
        """
        for name, field in self._fields.items():
            if hasattr(field, 'populate_obj_async'):
                await field.populate_obj_async(obj, name)
            else:
                field.populate_obj(obj, name)

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

    async def prefill(self, request: Request) -> None:
        for field in self:
            if isinstance(field, Prefill):
                await field.prefill(request, self)
