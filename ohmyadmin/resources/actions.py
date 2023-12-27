import enum
import typing

from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _

from ohmyadmin import htmx
from ohmyadmin.actions import actions, ActionVariant
from ohmyadmin.datasources.datasource import InFilter
from ohmyadmin.templating import render_to_response
from ohmyadmin.views import TableView

if typing.TYPE_CHECKING:
    from ohmyadmin.resources.resource import ResourceView


class SubmitActionType(enum.StrEnum):
    SAVE = "_save"
    SAVE_RETURN = "_save_return"


class CreateResourceAction(actions.Action):
    button_template: str = "ohmyadmin/actions/link.html"
    dropdown_template: str = "ohmyadmin/actions/link_menu.html"

    def __init__(self, label: str = _("Add new"), icon: str = "", variant: ActionVariant = "accent") -> None:
        self.icon = icon or self.icon
        self.label = label or self.label
        self.target = ""
        self.variant = variant

    def get_url(self, request: Request, model: typing.Any | None = None) -> URL:
        resource: ResourceView = request.state.resource
        return request.url_for(resource.get_create_route_name())


class EditResourceAction(actions.LinkAction):
    def __init__(self, label: str = _("Edit")) -> None:
        super().__init__(label=label, variant="default")

    def get_url(self, request: Request, object_id: typing.Any | None = None) -> URL:
        assert object_id, f"{self.__class__.__name__} can be used in model context only."
        resource: ResourceView = request.state.resource
        return request.url_for(resource.get_edit_route_name(), object_id=object_id)


class SaveResourceAction(actions.SubmitAction):
    def __init__(self, label: str = _("Save"), icon: str = "", variant: ActionVariant = "primary") -> None:
        super().__init__(label=label, icon=icon, variant=variant, name=SubmitActionType.SAVE)


class SaveResourceAndReturnAction(actions.SubmitAction):
    def __init__(self, label: str = _("Save and return"), icon: str = "", variant: ActionVariant = "default") -> None:
        super().__init__(label=label, icon=icon, variant=variant, name=SubmitActionType.SAVE_RETURN)


class ReturnToResourceIndexAction(actions.Action):
    button_template: str = "ohmyadmin/actions/link.html"
    dropdown_template: str = "ohmyadmin/actions/link_menu.html"

    def __init__(self, label: str = _("Cancel"), icon: str = "", variant: ActionVariant = "link") -> None:
        self.icon = icon or self.icon
        self.label = label or self.label
        self.target = ""
        self.variant = variant

    def get_url(self, request: Request) -> URL:
        resource: ResourceView = request.state.resource
        return request.url_for(resource.get_index_route_name())


class DeleteResourceAction(actions.ModalAction):
    modal_template: str = "ohmyadmin/resources/delete_action.html"

    def __init__(
        self, label: str = _("Delete", domain="ohmyadmin"), message: str = _("{count} objects has been deleted.")
    ) -> None:
        self.message = message
        super().__init__(label=label, dangerous=True)

    async def dispatch(self, request: Request) -> Response:
        resource: ResourceView = request.state.resource
        index_view: TableView = resource.index_view
        pk_field = resource.datasource.get_id_field()
        query = index_view.get_query(request)
        query = await index_view.apply_filters(request, query)
        if not self.all_selected(request):
            query = query.filter(InFilter(pk_field, self.get_object_ids(request)))
        total = await query.count(request)

        if request.method == "POST":
            message = self.message.format(count=total)
            await query.delete_all(request)
            return htmx.response().close_modal().toast(message).refresh()

        return render_to_response(
            request,
            self.modal_template,
            {
                "count": total,
                "action": self,
            },
        )
