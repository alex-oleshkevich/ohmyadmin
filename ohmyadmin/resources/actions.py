import enum
import typing

from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin import htmx
from ohmyadmin.actions import actions, ActionVariant
from ohmyadmin.actions.actions import ObjectIds
from ohmyadmin.datasources.datasource import InFilter
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens import DisplayScreen, TableScreen

if typing.TYPE_CHECKING:
    from ohmyadmin.resources.resource import ResourceScreen


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
        resource: ResourceScreen = request.state.resource
        return request.url_for(resource.get_create_route_name())


class EditResourceAction(actions.LinkAction):
    def __init__(self, label: str = _("Edit")) -> None:
        super().__init__(label=label, variant="default")

    def get_url(self, request: Request, model: typing.Any | None = None) -> URL:
        assert model, f"{self.__class__.__name__} can be used in model context only."
        resource: ResourceScreen = request.state.resource
        object_id = resource.datasource.get_pk(model)
        return request.url_for(resource.get_edit_route_name(), object_id=object_id)


class ViewResourceAction(actions.LinkAction):
    def __init__(self, label: str = _("View")) -> None:
        super().__init__(label=label, variant="default")

    def get_url(self, request: Request, model: typing.Any | None = None) -> URL:
        assert model, f"{self.__class__.__name__} can be used in model context only."
        resource: ResourceScreen = request.state.resource
        object_id = resource.datasource.get_pk(model)
        return request.url_for(resource.get_display_route_name(), object_id=object_id)


class SaveResourceAction(actions.SubmitAction):
    def __init__(self, label: str = _("Save"), icon: str = "", variant: ActionVariant = "primary") -> None:
        super().__init__(label=label, icon=icon, variant=variant, name=SubmitActionType.SAVE)


class SaveResourceAndReturnAction(actions.SubmitAction):
    def __init__(self, label: str = _("Save and return"), icon: str = "", variant: ActionVariant = "default") -> None:
        super().__init__(label=label, icon=icon, variant=variant, name=SubmitActionType.SAVE_RETURN)


class ReturnToResourceIndexAction(actions.LinkAction):
    def get_url(self, request: Request, model: typing.Any | None = None) -> URL:
        resource: ResourceScreen = request.state.resource
        return request.url_for(resource.get_index_route_name())


class DeleteResourceAction2(actions.ModalAction):
    modal_template: str = "ohmyadmin/resources/delete_action.html"

    def __init__(
        self, label: str = _("Delete", domain="ohmyadmin"), message: str = _("{count} objects has been deleted.")
    ) -> None:
        self.message = message
        super().__init__(label=label, dangerous=True)

    async def dispatch(self, request: Request) -> Response:
        resource: ResourceScreen = request.state.resource
        index_screen: TableScreen = resource.index_screen
        pk_field = resource.datasource.get_id_field()
        query = index_screen.get_query(request)
        query = await index_screen.apply_filters(request, query)
        if not self.all_selected(request):
            query = query.filter(InFilter(pk_field, self.get_object_ids(request)))
        total = await query.count(request)

        if request.method == "POST":
            message = self.message.format(count=total)
            await query.delete_all(request)
            if isinstance(request.state.screen, DisplayScreen):
                flash(request).success(message)
                redirect_to = request.url_for(resource.get_index_route_name())
                return htmx.response().location(redirect_to)
            return htmx.response().close_modal().toast(message).refresh()

        return render_to_response(
            request,
            self.modal_template,
            {"count": total, "action": self},
        )


class DeleteResourceAction(actions.NewAction):
    dangerous = True
    label = _("Delete")

    async def apply(self, request: Request, object_ids: ObjectIds) -> Response:
        pk_field = request.state.resource.datasource.get_id_field()
        query = request.state.resource.datasource
        if object_ids == "__all__":
            await query.delete_all()
        else:
            query = query.filter(InFilter(pk_field, object_ids))

        count = await query.count(request)
        await query.delete_all(request)
        return htmx.response().close_modal().toast(_("{count} objects deleted".format(count=count))).refresh()
