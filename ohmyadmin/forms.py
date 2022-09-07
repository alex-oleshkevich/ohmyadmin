from __future__ import annotations

import abc
import inspect
import typing
import wtforms
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import Receive, Scope, Send

from ohmyadmin.helpers import render_to_response, render_to_string

Choices = typing.Iterable[tuple[str, str]]
SyncChoices = typing.Callable[[Request], Choices]
AsyncChoices = typing.Callable[[Request], typing.Awaitable[Choices]]
Validator = typing.Callable[[wtforms.Field, wtforms.Field], typing.Awaitable[None] | None]


class Form(wtforms.Form):
    _creation_counter = 0
    _fields: dict[str, wtforms.Field]

    def __init__(
        self,
        request: Request,
        form_data: FormData | None = None,
        instance: typing.Any | None = None,
        prefix: str = '',
        data: typing.Mapping | None = None,
    ) -> None:
        self.request = request
        super().__init__(formdata=form_data, obj=instance, prefix=prefix, data=data)

    @classmethod
    async def from_request(
        cls,
        request: Request,
        instance: typing.Any | None = None,
        data: typing.Mapping | None = None,
    ) -> Form:
        form_data: FormData | None = None
        if request.method == 'POST':
            form_data = await request.form()
        form = cls(request=request, form_data=form_data, instance=instance, data=data)

        # process choices
        for name, field in form._fields.items():
            if choices_factory := getattr(field, 'choices_factory', None):
                if inspect.iscoroutinefunction(choices_factory):
                    field.choices = await choices_factory(request)
                elif callable(choices_factory):
                    field.choices = choices_factory(request)
                else:
                    field.choices = choices_factory.copy()

                empty_choice = getattr(field, 'empty_choice', None)
                if empty_choice is not None:
                    field.choices.insert(0, ('', empty_choice))

        return form

    @classmethod
    def from_layout(cls, layout: list[Layout], name: str | None = None) -> typing.Type[Form]:
        fields = []
        for element in layout:
            fields.extend(list(element.get_form_fields()))

        cls._creation_counter += 1
        name = name or f'AutoForm{cls._creation_counter}'
        form_fields = {field.name: field.create_form_field() for field in fields}
        form_class = type(name, (Form,), form_fields)
        return typing.cast(typing.Type[Form], form_class)

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


class Layout(abc.ABC):
    template = ''

    def get_form_fields(self) -> typing.Iterable[Field]:
        raise NotImplementedError()

    def render(self, request: Request) -> str:
        if not self.template:
            raise ValueError(f'Layout {self.__class__.__name__} does not define template name.')
        return render_to_string(request, self.template, {'request': request, 'element': self})


class Field(Layout):
    template = 'ohmyadmin/forms/field.html'
    field_class: typing.Type[wtforms.Field] = wtforms.StringField

    def __init__(
        self,
        name: str,
        *,
        label: str = '',
        required: bool = False,
        help_text: str = '',
        read_only: bool = False,
        default: typing.Any = None,
        validators: typing.Iterable[Validator] | None = None,
        widget_attrs: dict[str, str | bool] | None = None,
        template: str | None = None,
    ) -> None:
        self.name = name
        self.label = label or name.replace('_', ' ').title()
        self.help_text = help_text
        self.default = default
        self.read_only = read_only
        self.validators = validators or []
        self.required = required
        self.widget_attrs = widget_attrs or {}
        self.template = template or self.template

        # this value will be set on form construction
        self.form_field: wtforms.Field | None = None

    def get_validators(self) -> typing.Iterable[Validator]:
        for validator in self.validators:
            yield validator

        if self.required:
            yield wtforms.validators.data_required()

    def get_widget_attrs(self) -> dict[str, str | bool]:
        attrs = self.widget_attrs
        if self.required:
            attrs['required'] = ''
        if self.read_only:
            attrs['readonly'] = ''
        return attrs

    def get_form_fields(self) -> typing.Iterable[Field]:
        yield self

    def get_form_field_options(self) -> dict[str, typing.Any]:
        return {}

    def create_form_field(self) -> wtforms.Field:
        field = self.field_class(
            label=self.label,
            default=self.default,
            description=self.help_text,
            validators=list(self.get_validators()),
            render_kw=self.get_widget_attrs(),
            **self.get_form_field_options(),
        )
        original_binder = getattr(field, 'bind')

        def binder(*args: typing.Any, **kwargs: typing.Any) -> wtforms.Field:
            self.form_field = original_binder(*args, **kwargs)
            return self.form_field

        setattr(field, 'bind', binder)
        return field

    def render(self, request: Request) -> str:
        return render_to_string(request, self.template, {'field': self})

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: name={self.name}, label={self.label}>'


class CheckboxField(Field):
    template = 'ohmyadmin/forms/checkbox.html'
    field_class = wtforms.BooleanField


class TextField(Field):
    inputmode: str = 'text'

    def __init__(
        self,
        name: str,
        *,
        label: str = '',
        required: bool = False,
        placeholder: str = '',
        help_text: str = '',
        read_only: bool = False,
        default: typing.Any = None,
        validators: typing.Iterable[Validator] | None = None,
        autocomplete: str = '',
        inputmode: str = '',
        widget_attrs: dict[str, str | bool] | None = None,
    ) -> None:
        widget_attrs = widget_attrs or {}
        inputmode = inputmode or self.inputmode
        widget_attrs['inputmode'] = inputmode or self.inputmode

        if autocomplete:
            widget_attrs['autocomplete'] = autocomplete
        if placeholder:
            widget_attrs['placeholder'] = placeholder

        super().__init__(
            name,
            label=label,
            required=required,
            help_text=help_text,
            read_only=read_only,
            default=default,
            validators=validators,
            widget_attrs=widget_attrs,
        )


class PasswordField(TextField):
    field_class = wtforms.PasswordField


class EmailField(TextField):
    inputmode = 'email'
    field_class = wtforms.EmailField


class URLField(TextField):
    inputmode = 'url'
    field_class = wtforms.URLField


class IntegerField(TextField):
    inputmode = 'numeric'
    field_class = wtforms.IntegerField

    def __init__(
        self,
        name: str,
        *,
        min: int | None = None,
        max: int | None = None,
        step: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.min = min
        self.max = max
        self.step = step

        super().__init__(name, **kwargs)

    def get_widget_attrs(self) -> dict[str, str | bool]:
        attrs = super().get_widget_attrs()
        if self.min is not None:
            attrs['min'] = str(self.min)
        if self.max is not None:
            attrs['max'] = str(self.max)
        if self.step is not None:
            attrs['step'] = str(self.step)
        return attrs


class FloatField(TextField):
    inputmode = 'numeric'
    field_class = wtforms.FloatField

    def __init__(
        self,
        name: str,
        *,
        min: float | None = None,
        max: float | None = None,
        step: float | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.min = min
        self.max = max
        self.step = step
        super().__init__(name, **kwargs)

    def get_validators(self) -> typing.Iterable[Validator]:
        yield from super().get_validators()
        if self.min or self.max:
            yield wtforms.validators.number_range(min=self.min, max=self.max)


class DecimalField(FloatField):
    inputmode = 'decimal'
    field_class = wtforms.DecimalField

    def __init__(
        self,
        name: str,
        *,
        places: int = 2,
        rounding: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.places = places
        self.rounding = rounding
        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        options = super().get_form_field_options()
        options.update({'places': self.places, 'rounding': self.rounding})
        return options


class TelField(TextField):
    inputmode = 'tel'
    field_class = wtforms.TelField


class IntegerRangeField(Field):
    field_class = wtforms.IntegerRangeField


class DecimalRangeField(Field):
    field_class = wtforms.DecimalRangeField


class FileField(Field):
    field_class = wtforms.FileField


class MultipleFileField(Field):
    field_class = wtforms.MultipleFileField


class HiddenField(Field):
    field_class = wtforms.HiddenField


class DateTimeField(Field):
    field_class = wtforms.DateTimeLocalField

    def get_form_field_options(self) -> dict[str, typing.Any]:
        options = super().get_form_field_options()
        options.setdefault(
            'format',
            [
                "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
            ],
        )
        return options


class DateField(Field):
    field_class = wtforms.DateField


class TimeField(Field):
    field_class = wtforms.TimeField


class MonthField(Field):
    field_class = wtforms.MonthField


class NestedField(Field):
    field_class = wtforms.FormField

    def __init__(self, name: str, *, form_class: typing.Type[Form], **kwargs: typing.Any) -> None:
        self.form_class = form_class
        super().__init__(name, **kwargs)


# ListField = FieldList


class _SelectFormField(wtforms.SelectField):
    def __init__(
        self,
        label: str | None = None,
        validators: list[Validator] | None = None,
        coerce: typing.Callable = str,
        choices: Choices | None = None,
        validate_choice: bool = True,
        **kwargs: typing.Any,
    ):
        self.choices_factory = choices
        self.empty_choice = kwargs.pop('empty_choice', None)
        super().__init__(label, validators, coerce, validate_choice=validate_choice, **kwargs)


class SelectField(Field):
    field_class = _SelectFormField

    def __init__(
        self,
        name: str,
        *,
        choices: Choices | SyncChoices | AsyncChoices | None = None,
        coerce: typing.Callable = str,
        empty_choice: str | None = '',
        **kwargs: typing.Any,
    ) -> None:
        self.choices = choices or []
        self.coerce = coerce
        self.empty_choice = empty_choice

        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        return {'choices': self.choices, 'coerce': self.coerce, 'empty_choice': self.empty_choice}


class _SelectMultipleField(wtforms.SelectMultipleField):
    def __init__(
        self,
        label: str | None = None,
        validators: list[Validator] | None = None,
        coerce: typing.Callable = str,
        choices: Choices | None = None,
        validate_choice: bool = True,
        **kwargs: typing.Any,
    ):
        self.choices_factory = choices
        super().__init__(label, validators, coerce, validate_choice=validate_choice, **kwargs)


class SelectMultipleField(Field):
    field_class = _SelectMultipleField

    def __init__(
        self,
        name: str,
        *,
        choices: Choices | SyncChoices | AsyncChoices | None = None,
        coerce: typing.Callable = str,
        **kwargs: typing.Any,
    ) -> None:
        self.choices = choices or []
        self.coerce = coerce

        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        return {'choices': self.choices, 'coerce': self.coerce}


class _RadioFormField(wtforms.RadioField):
    def __init__(
        self,
        label: str | None = None,
        validators: list[Validator] | None = None,
        coerce: typing.Callable = str,
        choices: Choices | None = None,
        validate_choice: bool = True,
        **kwargs: typing.Any,
    ):
        self.choices_factory = choices
        super().__init__(label, validators, coerce, validate_choice=validate_choice, **kwargs)


class RadioField(Field):
    field_class = _RadioFormField
    template = 'ohmyadmin/forms/radio.html'

    def __init__(
        self,
        name: str,
        *,
        choices: Choices | SyncChoices | AsyncChoices | None = None,
        coerce: typing.Callable = str,
        **kwargs: typing.Any,
    ) -> None:
        self.choices = choices or []
        self.coerce = coerce

        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        return {'choices': self.choices, 'coerce': self.coerce}


class TextareaField(Field):
    field_class = wtforms.TextAreaField


class FormView:
    label: str = 'Edit'
    form_layout: list[Layout] = []

    def __init__(self, dbsession: sessionmaker) -> None:
        self.dbsession = dbsession

    def get_layout(self) -> list[Layout]:
        return self.form_layout

    async def handle_form(self, request: Request, form: wtforms.Form) -> Response:
        pass

    async def view(self, request: Request) -> Response:
        form_layout = self.get_layout()
        form_class = Form.from_layout(form_layout)
        form = await form_class.from_request(request)
        if await form.validate_on_submit(request):
            await self.handle_form(request, form)
            return RedirectResponse(request.headers.get('referer'), 302)

        return render_to_response(
            request,
            'ohmyadmin/form.html',
            {
                'request': request,
                'page_title': self.label,
                'layout': form_layout,
            },
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self.dbsession() as session:
            request = Request(scope, receive, send)
            request.state.db = session
            response = await self.view(request)
            await response(scope, receive, send)
