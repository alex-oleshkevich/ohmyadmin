import anyio
import inspect
import typing
import wtforms
from starlette.datastructures import FormData
from starlette.requests import Request

from ohmyadmin.collection import Collection
from ohmyadmin.utils import run_async
from ohmyadmin.validators import Validator

_F = typing.TypeVar('_F', bound=wtforms.Form)

SUBMIT_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']


class Form(wtforms.Form):
    @classmethod
    async def from_request(
        cls: typing.Type[_F],
        request: Request,
        obj: typing.Any | None = None,
        prefix: str = '',
        data: typing.Mapping | None = None,
        meta: typing.Mapping | None = None,
        extra_filters: typing.Mapping | None = None,
    ) -> tuple[_F, FormData]:
        form_data = FormData()
        if request.method in SUBMIT_METHODS:
            form_data = await request.form()
        form = cls(
            request=request,
            formdata=form_data,
            obj=obj,
            prefix=prefix,
            data=data,
            meta=meta,
            extra_filters=extra_filters,
        )

        # setup choices
        for name, field in form._fields.items():
            if populator := getattr(form, f'choices_for_{name}', None):
                value = await run_async(populator, request)
                if isinstance(value, Collection):
                    value = value.choices()
                getattr(form, name).choices = value

        return form, form_data

    def is_submitted(self, request: Request) -> bool:
        return request.method in SUBMIT_METHODS

    async def validate(self, request: Request) -> bool:
        extra_validators: dict[str, list[Validator]] = {}

        async_validators = []
        for name, field in self._fields.items():
            if validator := getattr(self, f'validator_for_{name}', None):
                if inspect.iscoroutinefunction(validator):
                    async_validators.append([field, validator])
                else:
                    extra_validators.setdefault(name, []).append(validator)

        is_valid = super().validate(extra_validators)
        completed = []

        async def _perform_field_validation(field: wtforms.Field, validator: Validator) -> None:
            is_valid = await self._validate_field(request, field, validator)
            completed.append(is_valid)

        async with anyio.create_task_group() as tg:
            for field, validator in async_validators:
                tg.start_soon(_perform_field_validation, field, validator)

        if False in completed:
            is_valid = False
        return is_valid

    async def _validate_field(self, request: Request, field: wtforms.Field, validator: Validator) -> bool:
        try:
            await validator(request, self, field)
            return True
        except wtforms.ValidationError as ex:
            field.errors.append(ex.args[0])
            return False

    async def validate_on_submit(self, request: Request) -> bool:
        return self.is_submitted(request) and await self.validate(request)
