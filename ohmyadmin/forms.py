from __future__ import annotations

import abc
import datetime
import decimal
import inspect
import typing
import wtforms
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import Receive, Scope, Send
from wtforms.fields.core import UnboundField
from wtforms.utils import unset_value

from ohmyadmin.actions import Action, SubmitAction
from ohmyadmin.helpers import render_to_response, render_to_string

Choices = typing.Iterable[tuple[str, str]]
SyncChoices = typing.Callable[[], Choices]
Validator = typing.Callable[[wtforms.Field, wtforms.Field], typing.Awaitable[None] | None]


class Layout(abc.ABC):
    template = ''

    def render(self) -> str:
        if not self.template:
            raise ValueError(f'Layout {self.__class__.__name__} does not define template name.')
        return render_to_string(self.template, {'element': self})

    __str__ = render


class Grid(Layout):
    template = 'ohmyadmin/forms/layout_grid.html'

    def __init__(self, children: typing.Iterable[Layout], cols: int = 2, gap: int = 5) -> None:
        self.cols = cols
        self.gap = gap
        self.children = children

    def __iter__(self) -> typing.Iterator[Layout]:
        return iter(self.children)


class FormLayout(Layout):
    template = 'ohmyadmin/forms/layout_form.html'

    def __init__(self, child: Layout, actions: list[Action]) -> None:
        self.child = child
        self.actions = actions


class FormField(Layout):
    template = 'ohmyadmin/forms/layout_field.html'

    def __init__(self, field: wtforms.Field) -> None:
        self.field = field


T = typing.TypeVar('T')


class Field(typing.Generic[T], wtforms.Field):
    template = 'ohmyadmin/forms/field.html'
    data: T

    def __init__(
        self,
        attr_name: str,
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
        self.attr_name = attr_name
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
        return f'<{self.__class__.__name__}: name={self.attr_name}>'


class CheckboxField(Field[bool], wtforms.BooleanField):
    template = 'ohmyadmin/forms/checkbox.html'


class TextField(Field[str], wtforms.StringField):
    inputmode: str = 'text'
    template = 'ohmyadmin/forms/text.html'

    def __init__(
        self,
        attr_name: str,
        *,
        placeholder: str = '',
        autocomplete: str = '',
        inputmode: str = '',
        **kwargs: typing.Any,
    ) -> None:
        widget_attrs = kwargs.pop('widget_attrs', {})
        inputmode = inputmode or self.inputmode
        if inputmode:
            widget_attrs['inputmode'] = inputmode
        if autocomplete:
            widget_attrs['autocomplete'] = autocomplete
        if placeholder:
            widget_attrs['placeholder'] = placeholder

        super().__init__(attr_name, widget_attrs=widget_attrs, **kwargs)


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
        attr_name: str,
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

        super().__init__(attr_name, validators=validators, widget_attrs=attrs, **kwargs)


class FloatField(Field[float], wtforms.FloatField):
    inputmode = 'numeric'
    template = 'ohmyadmin/forms/float.html'
    widget = wtforms.widgets.NumberInput()

    def __init__(
        self,
        attr_name: str,
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

        super().__init__(attr_name, validators=validators, widget_attrs=attrs, **kwargs)


class DecimalField(FloatField):
    inputmode = 'decimal'
    template = 'ohmyadmin/forms/decimal.html'


class TelField(TextField, wtforms.TelField):
    inputmode = 'tel'
    template = 'ohmyadmin/forms/tel.html'


class IntegerRangeField(Field[int], wtforms.IntegerRangeField):
    template = 'ohmyadmin/forms/integer_range.html'


class DecimalRangeField(Field[decimal.Decimal], wtforms.DecimalRangeField):
    template = 'ohmyadmin/forms/decimal_range.html'


class FileField(Field[UploadFile], wtforms.FileField):
    template = 'ohmyadmin/forms/file.html'


class MultipleFileField(Field[list[UploadFile]], wtforms.MultipleFileField):
    template = 'ohmyadmin/forms/file_multiple.html'


class HiddenField(Field[typing.Any], wtforms.HiddenField):
    template = 'ohmyadmin/forms/hidden.html'


class DateTimeField(Field[datetime.datetime], wtforms.DateTimeLocalField):
    template = 'ohmyadmin/forms/datetime.html'

    def __init__(self, attr_name: str, *, format: list[str] | None = None, **kwargs: typing.Any) -> None:
        format = format or [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]
        super().__init__(attr_name, format=format, **kwargs)


class DateField(Field[datetime.date], wtforms.DateField):
    template = 'ohmyadmin/forms/date.html'

    def __init__(self, attr_name: str, *, format: str = "%Y-%m-%d", **kwargs: typing.Any) -> None:
        super().__init__(attr_name, format=format, **kwargs)


class TimeField(Field[datetime.time], wtforms.TimeField):
    template = 'ohmyadmin/forms/time.html'


class MonthField(Field[datetime.date], wtforms.MonthField):
    template = 'ohmyadmin/forms/month.html'

    def __init__(self, attr_name: str, *, format: str = "%Y-%m", **kwargs: typing.Any) -> None:
        super().__init__(attr_name, format=format, **kwargs)


class TextareaField(Field[str], wtforms.TextAreaField):
    template = 'ohmyadmin/forms/textarea.html'

    def __init__(
        self,
        attr_name: str,
        *,
        placeholder: str = '',
        min_length: int = -1,
        max_length: int = -1,
        **kwargs: typing.Any,
    ) -> None:
        widget_attrs = kwargs.pop('widget_attrs', {})
        if placeholder:
            widget_attrs['placeholder'] = placeholder

        validators = kwargs.pop('validators', [])
        if min_length or max_length:
            validators.append(wtforms.validators.length(min=min_length, max=max_length))

        super().__init__(attr_name, validators=validators, widget_attrs=widget_attrs, **kwargs)


class SelectField(Field[typing.Any], wtforms.SelectField):
    template = 'ohmyadmin/forms/select.html'

    def __init__(
        self,
        attr_name: str,
        *,
        choices: Choices | SyncChoices | None = None,
        coerce: typing.Callable = str,
        empty_choice: str | None = '',
        **kwargs: typing.Any,
    ) -> None:
        coerce = coerce
        choices = list(choices() if callable(choices) else (choices or []))
        if empty_choice:
            choices.insert(0, ('', empty_choice))

        super().__init__(attr_name, choices=choices, coerce=coerce, **kwargs)


class SelectMultipleField(Field[list[typing.Any]], wtforms.SelectMultipleField):
    template = 'ohmyadmin/forms/select_multiple.html'

    def __init__(
        self,
        attr_name: str,
        *,
        choices: Choices | SyncChoices | None = None,
        coerce: typing.Callable = str,
        **kwargs: typing.Any,
    ) -> None:
        coerce = coerce
        choices = choices() if callable(choices) else choices or []

        super().__init__(attr_name, choices=choices, coerce=coerce, **kwargs)


class RadioField(Field[typing.Any], wtforms.RadioField):
    template = 'ohmyadmin/forms/radio.html'


class ListField(Field[typing.Any], wtforms.FieldList):
    template = 'ohmyadmin/forms/list.html'

    def __init__(
        self,
        attr_name: str,
        unbound_field: UnboundField,
        min_entries: int = 1,
        max_entries: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        kwargs.setdefault('default', [])
        super().__init__(
            attr_name,
            unbound_field=unbound_field,
            min_entries=min_entries,
            max_entries=max_entries,
            **kwargs,
        )

    def create_empty_entry(self) -> Form:
        id = "%s%s${index}" % (self.id, self._separator)
        name = "%s%s${index}" % (self.short_name, self._separator)
        field = self.unbound_field.bind(
            form=None,
            id=id,
            name=name,
            prefix=self._prefix,
            _meta=self.meta,
            translations=self._translations,
        )
        field.process(None)
        field.render_kw['x-bind:id'] = "`{}`".format(id)
        field.render_kw['x-bind:name'] = "`{}`".format(name)
        return field

    def _add_entry(
        self, formdata: FormData | None = None, data: typing.Any = unset_value, index: int | None = None
    ) -> wtforms.Field:
        field: wtforms.Field = super()._add_entry(formdata, data, index)
        field.render_kw['x-bind:id'] = "`{}`".format(field.id.replace(str(index), '${index}'))
        field.render_kw['x-bind:name'] = "`{}`".format(field.name.replace(str(index), '${index}'))
        return field


class EmbedField(Field[T], wtforms.FormField):
    template = 'ohmyadmin/forms/embed.html'

    def __init__(
        self,
        attr_name: str,
        form_class: typing.Type[Form],
        cols: int = 2,
        **kwargs: typing.Any,
    ) -> None:
        self.cols = cols
        super().__init__(attr_name, form_class=form_class, **kwargs)


class EmbedManyField(Field[list[T]], wtforms.FieldList):
    field_class = wtforms.FieldList
    template = 'ohmyadmin/forms/embed_many.html'

    def __init__(
        self,
        attr_name: str,
        form_class: typing.Type[Form],
        min_entries: int = 1,
        max_entries: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.form_class = form_class
        kwargs.setdefault('default', [])
        super().__init__(
            attr_name,
            unbound_field=wtforms.FormField(form_class),
            min_entries=min_entries,
            max_entries=max_entries,
            **kwargs,
        )

    def create_empty_entry(self) -> Form:
        id = "%s%s${index}" % (self.id, self._separator)
        name = "%s%s${index}" % (self.short_name, self._separator)
        form = self.form_class(
            form=None,
            id=id,
            name=name,
            prefix=self._prefix,
            _meta=self.meta,
            translations=self._translations,
        )
        form.process(None)
        for index, field in enumerate(form):
            field.render_kw['x-bind:id'] = f"`{id}{self._separator}{field.id}`"
            field.render_kw['x-bind:name'] = f"`{name}{self._separator}{field.name}`"
        return form

    def _add_entry(
        self, formdata: FormData | None = None, data: typing.Any = unset_value, index: int | None = None
    ) -> wtforms.Form:
        field: wtforms.FormField = super()._add_entry(formdata, data, index)
        for index, field in enumerate(field):
            field.render_kw['x-bind:id'] = "`{}`".format(field.id.replace(str(index), '${index}'))
            field.render_kw['x-bind:name'] = "`{}`".format(field.name.replace(str(index), '${index}'))
        return field


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
    def from_fields(cls, fields: typing.Iterable[UnboundField]) -> typing.Type[Form]:
        cls._creation_counter += 1
        form_class = type(f'AutoForm{cls._creation_counter}', (cls,), {})
        for field in fields:
            setattr(form_class, field.args[0], field)
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
        fields: typing.Iterable[UnboundField],
        instance: typing.Any | None = None,
        data: dict[str, typing.Any] | None = None,
    ) -> Form:
        form_class = cls.from_fields(fields)
        return await form_class.from_request(request, instance=instance, data=data)


class FormView:
    label: str = 'Edit'
    form_fields: list[UnboundField] | None = None

    def __init__(self, dbsession: sessionmaker) -> None:
        self.dbsession = dbsession

    def get_form_fields(self) -> typing.Iterable[UnboundField]:
        return list(self.form_fields or [])

    async def handle_form(self, request: Request, form: wtforms.Form) -> Response:
        print(form.data)
        return Response('form handled')

    def get_layout(self, form: Form) -> Layout:
        return FormLayout(
            child=Grid([FormField(field) for field in form], cols=1),
            actions=[
                SubmitAction('Save', color='primary'),
                SubmitAction('Save and return to list'),
                SubmitAction('Save and add new'),
            ],
        )

    async def view(self, request: Request) -> Response:
        form = await Form.new(request, fields=self.get_form_fields())
        layout = self.get_layout(form)

        if await form.validate_on_submit(request):
            await self.handle_form(request, form)
            return RedirectResponse(request.headers.get('referer'), 302)

        return render_to_response(
            request,
            'ohmyadmin/form.html',
            {
                'request': request,
                'page_title': self.label,
                'layout': layout,
            },
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self.dbsession() as session:
            request = Request(scope, receive, send)
            request.state.db = session
            response = await self.view(request)
            await response(scope, receive, send)
