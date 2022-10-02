import datetime
import inspect
import os.path
import random
import string
import time
import typing
import wtforms
from starlette.datastructures import FormData, UploadFile
from wtforms.utils import unset_value

from ohmyadmin.storage import FileStorage

UploadFilename = typing.Callable[[UploadFile, typing.Any], str]


class Uploader:
    def __init__(self, storage: FileStorage, upload_to: str | UploadFilename) -> None:
        self.storage = storage
        self.destination = upload_to

    def generate_filename(self, entity: typing.Any, upload_file: UploadFile) -> str:
        prefix = ''.join(random.choices(string.ascii_lowercase, k=6))
        file_name, ext = os.path.splitext(upload_file.filename)
        timestamp = time.time()
        current_date = datetime.datetime.now().date().isoformat()
        current_time = datetime.datetime.now().time().isoformat()

        destination = self.destination if isinstance(self.destination, str) else self.destination(upload_file, entity)
        pk = ''
        if '{pk}' in destination:
            if hasattr(entity, 'get_pk'):
                pk = entity.get_pk()
            else:
                raise AttributeError(
                    f'File uploader uses {{pk}} format in file path '
                    f'but entity class {entity.__class__.__name__} does not define `get_pk() -> str` method. '
                    f'Please, define this method first.'
                )

        return destination.format(
            pk=pk,
            original_name=upload_file.filename,
            prefix=prefix,
            ext=ext,
            name=file_name,
            timestamp=timestamp,
            date=current_date,
            time=current_time,
        )

    async def delete(self, path: str) -> None:
        await self.storage.delete(path)

    async def upload(self, upload_file: UploadFile, path: str) -> str:
        return await self.storage.write(path, upload_file)


StringField = wtforms.StringField
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
        validators: typing.Callable[[wtforms.Form, wtforms.Field], None] = None,
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

    def process(self, formdata: FormData, data: str = unset_value, extra_filters: typing.Callable = None) -> None:
        if formdata:
            marker = '%s-delete' % self.name
            if marker in formdata:
                self._should_delete = True

        super().process(formdata, data, extra_filters)  # noqa

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

    async def populate_obj_async(self, obj: typing.Any, name: str) -> None:
        field = getattr(obj, name, None)
        if field:
            if self._should_delete:
                await self._delete_file(field)
                setattr(obj, name, None)
                return

        if self._is_uploaded_file(self.data):
            if field:
                await self._delete_file(field)

            assert self.data
            filename = self.uploader.generate_filename(obj, self.data)
            filename = await self.uploader.upload(self.data, filename)
            self.data.filename = filename

            setattr(obj, name, filename)

    def _is_uploaded_file(self, value: UploadFile | None) -> bool:
        return bool(value and isinstance(value, UploadFile) and value.filename)

    async def _delete_file(self, path: str) -> None:
        await self.uploader.delete(path)


class MultipleFileField(wtforms.MultipleFileField):
    ...


class ImageField(wtforms.FileField):
    ...


class DropZoneField(wtforms.FileField):
    ...


class SelectField(wtforms.SelectField):
    ...


class BooleanField(wtforms.BooleanField):
    ...


class RadioField(wtforms.RadioField):
    ...


class FieldList(wtforms.FieldList):
    ...


class FormField(wtforms.FormField):
    ...


class JSONField(wtforms.TextAreaField):
    ...


class CodeField(wtforms.TextAreaField):
    ...


class Form(wtforms.Form):
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
