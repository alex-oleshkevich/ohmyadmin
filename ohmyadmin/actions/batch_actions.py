import typing

import wtforms
from starlette.requests import Request
from starlette.responses import Response


BatchActionHandler = typing.Callable[
    [Request, typing.Sequence[str], wtforms.Form], typing.Awaitable[Response]
]


class BatchAction:
    label: typing.ClassVar[str] = ""
    dangerous: bool = False
    template: str = "ohmyadmin/actions/batch_action_modal.html"


# class ObjectAction(WithRoute, Dispatchable):
#     callback: BatchActionHandler
#     icon: str = ""
#     slug: str = ""
#     title: str = ""
#     description: str = ""
#     dangerous: bool = False
#     template: str = "ohmyadmin/actions/batch_action_modal.html"
#     form_class: typing.Type[wtforms.Form] = wtforms.Form
#     label: str = dataclasses.field(default_factory=lambda: _("Unlabeled"))
#
#     def get_slug(self) -> str:
#         return self.slug or slugify(self.label or str(id(self)))
#
#     async def dispatch(self, request: Request) -> Response:
#         form = await create_form(request, self.form_class)
#         if await validate_on_submit(request, form):
#             selected = request.query_params.getlist('selected')
#             return await self.callback(request, selected, form)
#
#         return render_to_response(request, self.template, {"form": form, "action": self})
