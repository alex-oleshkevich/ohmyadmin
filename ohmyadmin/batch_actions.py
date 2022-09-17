from __future__ import annotations

import abc
import json
import re
import sqlalchemy as sa
import typing
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.types import Receive, Scope, Send

from ohmyadmin.actions import ActionResponse
from ohmyadmin.components import Component, FormElement, Grid
from ohmyadmin.flash import flash
from ohmyadmin.forms import Form
from ohmyadmin.helpers import render_to_response
from ohmyadmin.i18n import _
from ohmyadmin.responses import Response

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import PkType


class BatchActionMeta(abc.ABCMeta):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        name = name.removesuffix('Action')
        label = re.sub(r'(?<!^)(?=[A-Z])', ' ', name).title()

        attrs['id'] = attrs.get('id', name.lower())
        attrs['label'] = attrs.get('label', label)
        return super().__new__(cls, name, bases, attrs)


class BatchAction(abc.ABC, metaclass=BatchActionMeta):
    id: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = 'Unlabelled'
    confirmation: typing.ClassVar[str] = ''
    dangerous: typing.ClassVar[bool] = False
    template: str = 'ohmyadmin/tables/batch_action.html'
    form_class: typing.ClassVar[typing.Type[Form]] = Form

    Result = ActionResponse

    @abc.abstractmethod
    async def apply(self, request: Request, ids: list[PkType], form: Form) -> ActionResponse:
        ...

    async def dispatch(self, request: Request) -> Response:
        form = await self.get_form_class().from_request(request)
        if await form.validate_on_submit(request):
            form_data = await request.form()
            resource = request.state.resource
            object_ids = [resource.pk_type(typing.cast(str, object_id)) for object_id in form_data.getlist('selected')]
            result = await self.apply(request, object_ids, form)
            return self.result_to_response(request, result)

        layout = self.get_form_layout(form)
        return render_to_response(
            request,
            self.template,
            {
                'action': self,
                'form': layout,
                'resource': request.state.resource,
            },
        )

    def result_to_response(self, request: Request, result: ActionResponse) -> Response:
        match result:
            case ActionResponse(
                type=ActionResponse.Type.TOAST, toast_options=toast_options
            ) if toast_options is not None:
                return Response(status_code=204).add_header(
                    'HX-Trigger',
                    json.dumps(
                        {
                            'action_result.success': '',
                            'toast': {'message': toast_options.message, 'category': toast_options.category},
                        }
                    ),
                )

            case ActionResponse(
                type=ActionResponse.Type.REDIRECT, redirect_options=redirect_options
            ) if redirect_options is not None:
                if redirect_options.url:
                    url = redirect_options.url
                elif redirect_options.path_name:
                    path_params = redirect_options.path_params or {}
                    url = request.url_for(redirect_options.path_name, **path_params)
                elif redirect_options.resource:
                    url = request.url_for(redirect_options.resource.get_route_name(redirect_options.resource_action))
                else:
                    raise ValueError("Don't know the redirect destination.")
                response = Response(status_code=204).add_header('HX-Redirect', url)
                if result.toast_options is not None:
                    flash(request).add(result.toast_options.message, result.toast_options.category)
                return response

        return Response(status_code=204).add_header('HX-Refresh', 'true')

    def respond(self) -> typing.Type[ActionResponse]:
        return ActionResponse

    def get_form_layout(self, form: Form) -> Component:
        return Grid([FormElement(field) for field in form])

    def get_form_class(self) -> typing.Type[Form]:
        return getattr(self, 'ActionForm', self.form_class)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        response = await self.dispatch(request)
        await response(scope, receive, send)


class BulkDeleteAction(BatchAction):
    dangerous = True
    confirmation = _('Do you want to delete all items?')

    async def apply(self, request: Request, ids: list[PkType], params: FormData) -> ActionResponse:
        stmt = sa.select(request.state.resource.entity_class).where(
            sa.column(request.state.resource.pk_column).in_(ids)
        )
        result = await request.state.dbsession.scalars(stmt)
        for row in result.all():
            await request.state.dbsession.delete(row)

        return self.respond().redirect_to_resource(request.state.resource)
