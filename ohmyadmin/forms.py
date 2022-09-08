from __future__ import annotations

import abc
import copy
import inspect
import typing
import wtforms
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import Receive, Scope, Send

from ohmyadmin.helpers import render_to_response, render_to_string

Choices = typing.Iterable[tuple[str, str]]
SyncChoices = typing.Callable[[], Choices]
Validator = typing.Callable[[wtforms.Field, wtforms.Field], typing.Awaitable[None] | None]


class Layout(abc.ABC):
    template = ''

    def get_form_fields(self) -> typing.Iterable[Field]:
        raise NotImplementedError()

    def render(self) -> str:
        if not self.template:
            raise ValueError(f'Layout {self.__class__.__name__} does not define template name.')
        return render_to_string(self.template, {'element': self})

    __str__ = render


class Grid(Layout):
    template = 'ohmyadmin/forms/grid.html'

    def __init__(self, children: typing.Iterable[Layout], cols: int = 2, gap: int = 5) -> None:
        self.cols = cols
        self.gap = gap
        self.children = children

    def get_form_fields(self) -> typing.Iterable[Field]:
        yield from self.children

    def __iter__(self) -> typing.Iterator[Layout]:
        return iter(self.children)


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

    def render(self) -> str:
        return render_to_string(self.template, {'field': self})

    def clone_with(self, form_field: wtforms.Field | None = None) -> Field:
        clone = copy.deepcopy(self)
        if form_field:
            clone.form_field = form_field
        return clone

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: name={self.name}, label={self.label}>'

    __str__ = render
    __call__ = render


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


class ListField(Field):
    field_class = wtforms.FieldList
    template = 'ohmyadmin/forms/list.html'

    def __init__(
        self, name: str, field: Field, min_entries: int = 1, max_entries: int | None = None, **kwargs: typing.Any
    ) -> None:
        self.field = field
        self.min_entries = min_entries
        self.max_entries = max_entries
        kwargs.setdefault('default', [])
        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        options = super().get_form_field_options()
        options.update(
            {
                'min_entries': self.min_entries,
                'max_entries': self.max_entries,
                'unbound_field': self.field.create_form_field(),
            }
        )
        return options


class EmbedField(Field):
    field_class = wtforms.FormField
    template = 'ohmyadmin/forms/embed.html'

    def __init__(self, name: str, fields: typing.Iterable[Layout], cols: int = 2, **kwargs: typing.Any) -> None:
        self.cols = cols
        self.fields = list(collect_fields(fields))
        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        options = super().get_form_field_options()
        options.update({'form_class': create_wtf_form_class(self.fields)})
        return options

    def __iter__(self) -> typing.Iterator[Layout]:
        return iter(self.fields)


class EmbedManyField(Field):
    field_class = wtforms.FieldList
    template = 'ohmyadmin/forms/embed_many.html'

    def __init__(
        self,
        name: str,
        fields: typing.Iterable[Field],
        min_entries: int = 1,
        max_entries: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.min_entries = min_entries
        self.max_entries = max_entries
        self.fields = list(collect_fields(fields))
        kwargs.setdefault('default', [])
        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        form_class = create_wtf_form_class(self.fields)

        options = super().get_form_field_options()
        options.update(
            {
                'min_entries': self.min_entries,
                'max_entries': self.max_entries,
                'unbound_field': wtforms.FormField(form_class=form_class),
            }
        )
        return options


class SelectField(Field):
    field_class = wtforms.SelectField

    def __init__(
        self,
        name: str,
        *,
        choices: Choices | SyncChoices | None = None,
        coerce: typing.Callable = str,
        empty_choice: str | None = '',
        **kwargs: typing.Any,
    ) -> None:
        self.coerce = coerce
        self.choices = list(choices() if callable(choices) else (choices or []))
        if empty_choice:
            self.choices.insert(0, ('', empty_choice))

        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        return {'choices': self.choices, 'coerce': self.coerce}


class SelectMultipleField(Field):
    field_class = wtforms.SelectMultipleField

    def __init__(
        self,
        name: str,
        *,
        choices: Choices | SyncChoices | None = None,
        coerce: typing.Callable = str,
        **kwargs: typing.Any,
    ) -> None:
        self.coerce = coerce
        self.choices = choices() if callable(choices) else choices or []

        super().__init__(name, **kwargs)

    def get_form_field_options(self) -> dict[str, typing.Any]:
        return {'choices': self.choices, 'coerce': self.coerce}


class RadioField(SelectMultipleField):
    field_class = wtforms.RadioField
    template = 'ohmyadmin/forms/radio.html'


class TextareaField(Field):
    field_class = wtforms.TextAreaField


def create_wtf_form_class(fields: typing.Iterable[Field]) -> typing.Type[wtforms.Form]:
    counter = getattr(create_wtf_form_class, '_counter', 0) + 1
    setattr(create_wtf_form_class, '_counter', counter)
    form_class = type(
        f'AutoWtfForm{counter}', (wtforms.Form,), {field.name: field.create_form_field() for field in fields}
    )
    return typing.cast(typing.Type[wtforms.Form], form_class)


def collect_fields(layout: typing.Iterable[Layout]) -> typing.Iterable[Field]:
    for element in layout:
        yield from element.get_form_fields()


class Form(wtforms.Form):
    _creation_counter = 0

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

    @classmethod
    def from_fields(cls, fields: typing.Iterable[Field]) -> typing.Type[Form]:
        cls._creation_counter += 1
        form_class = type(
            f'AutoForm{cls._creation_counter}', (cls,), {field.name: field.create_form_field() for field in fields}
        )
        return typing.cast(typing.Type[Form], form_class)

    @classmethod
    async def from_request(
        cls,
        request: Request,
        instance: typing.Any | None = None,
        data: dict[str, typing.Any] | None = None,
    ) -> Form:
        form_data = await request.form() if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] else None
        return cls(formdata=form_data, obj=instance, data=data)

    @classmethod
    async def new(
        cls,
        request: Request,
        fields: typing.Iterable[Field],
        instance: typing.Any | None = None,
        data: dict[str, typing.Any] | None = None,
    ) -> Form:
        form_class = cls.from_fields(fields)
        return await form_class.from_request(request, instance=instance, data=data)


class FormView:
    label: str = 'Edit'
    form_fields: list[Field] | None = None

    def __init__(self, dbsession: sessionmaker) -> None:
        self.dbsession = dbsession

    def get_form_fields(self) -> typing.Iterable[Field]:
        return list(self.form_fields or [])

    async def handle_form(self, request: Request, form: wtforms.Form) -> Response:
        print(form.data)
        return Response('form handled')

    async def view(self, request: Request) -> Response:
        form = await Form.new(request, fields=self.get_form_fields())

        if await form.validate_on_submit(request):
            await self.handle_form(request, form)
            return RedirectResponse(request.headers.get('referer'), 302)

        return render_to_response(
            request,
            'ohmyadmin/form.html',
            {
                'request': request,
                'page_title': self.label,
                'layout': form,
            },
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self.dbsession() as session:
            request = Request(scope, receive, send)
            request.state.db = session
            response = await self.view(request)
            await response(scope, receive, send)
