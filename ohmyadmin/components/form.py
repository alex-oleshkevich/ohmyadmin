import typing
import wtforms
from starlette.datastructures import UploadFile
from starlette.requests import Request


class Uploader:
    def __init__(self) -> None:
        pass

    async def upload(self, request: Request, upload_file: UploadFile) -> str:
        pass


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
