import typing

import slugify
import wtforms
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount
from starlette_babel import gettext_lazy as _

from ohmyadmin import filters, htmx, metrics, views
from ohmyadmin.actions import actions
from ohmyadmin.components import AutoLayout, FormLayoutBuilder
from ohmyadmin.datasources.datasource import DataSource, DuplicateError, InFilter
from ohmyadmin.helpers import pluralize, snake_to_sentence
from ohmyadmin.menu import MenuItem
from ohmyadmin.resources.actions import (
    CreateResourceAction,
    DeleteResourceAction,
    EditResourceAction,
    ReturnToResourceIndexAction,
    SaveResourceAction,
    SaveResourceAndReturnAction,
    SubmitActionType,
)
from ohmyadmin.resources.policy import AccessPolicy, PermissiveAccessPolicy
from ohmyadmin.views.base import ExposeViewMiddleware, View
from ohmyadmin.views.table import Column


class ResourceView(View):
    label: str = ""
    label_plural: str = ""
    index_label: str = _("{label_plural}", domain="ohmyadmin")
    create_label: str = _("Create {label}", domain="ohmyadmin")
    edit_label: str = _("Edit {label}", domain="ohmyadmin")
    display_label: str = _("Edit {label}", domain="ohmyadmin")
    delete_label: str = _("Delete {label}?", domain="ohmyadmin")

    create_message: str = _('{label} "{object}" has been created!', domain="ohmyadmin")
    update_message: str = _('{label} "{object}" has been updated!', domain="ohmyadmin")
    delete_message: str = _('{label} "{object}" has been deleted!', domain="ohmyadmin")

    # menus
    create_resource_label: str = _("Add {label}", domain="ohmyadmin")
    edit_resource_label: str = _("Edit", domain="ohmyadmin")
    delete_resource_label: str = _("Edit", domain="ohmyadmin")
    create_resource_form_label: str = _("Create")
    create_and_return_resource_form_label: str = _("Create and return to list")
    update_resource_form_label: str = _("Update")
    update_and_return_resource_form_label: str = _("Update and return to list")
    cancel_resource_form_label: str = _("Cancel")

    # permissions
    access_policy: AccessPolicy = PermissiveAccessPolicy()

    # index page
    page_param: typing.ClassVar[str] = "page"
    page_size_param: typing.ClassVar[str] = "page_size"
    page_size: typing.ClassVar[int] = 25
    page_sizes: typing.ClassVar[typing.Sequence[int]] = [10, 25, 50, 100]
    ordering_param: typing.ClassVar[str] = "ordering"
    datasource: typing.ClassVar[DataSource | None] = None
    columns: typing.Sequence[Column] = tuple()
    page_filters: typing.Sequence[filters.Filter] = tuple()
    page_actions: typing.Sequence[actions.Action] = tuple()
    page_metrics: typing.Sequence[metrics.Metric] = tuple()
    object_actions: typing.Sequence[actions.Action] = tuple()
    batch_actions: typing.Sequence[actions.ModalAction] = tuple()
    search_param: str = "search"
    search_placeholder: str = ""

    # edit page
    form_class: type[wtforms.Form] = wtforms.Form
    form_layout_class: type[FormLayoutBuilder] = AutoLayout
    form_actions: typing.Sequence[actions.Action] = tuple()

    # create page
    create_form_class: type[wtforms.Form] | None = None
    create_form_layout_class: type[FormLayoutBuilder] | None = None
    create_form_actions: typing.Sequence[actions.Action] | None = None

    def __init__(self) -> None:
        assert self.datasource, f"Class {self.__class__.__name__} must have a datasource."
        self.label = self.label or snake_to_sentence(self.__class__.__name__.removesuffix("Resource"))
        self.label_plural = self.label_plural or pluralize(self.label)
        self.index_view = self.create_index_view_class()()
        self.edit_view = self.create_edit_view_class()()
        self.create_view = self.create_create_view_class()()

    @property
    def slug(self) -> str:
        return slugify.slugify(self.label_plural)

    def get_index_page_actions(self) -> list[actions.Action]:
        """Return user defined actions along with default actions."""
        return [
            *self.page_actions,
            CreateResourceAction(
                label=self.create_resource_label.format(label=self.label, label_plural=self.label_plural),
            ),
        ]

    def get_object_actions(self) -> list[actions.Action]:
        return [
            *self.object_actions,
            EditResourceAction(label=self.edit_resource_label.format(label=self.label, label_plural=self.label_plural)),
            DeleteResourceAction(),
        ]

    def get_create_form_actions(self) -> list[actions.Action]:
        return self.create_form_actions or [
            SaveResourceAction(label=self.create_resource_form_label),
            SaveResourceAndReturnAction(label=self.create_and_return_resource_form_label),
            ReturnToResourceIndexAction(label=self.cancel_resource_form_label),
        ]

    def get_edit_form_actions(self) -> list[actions.Action]:
        return self.form_actions or [
            SaveResourceAction(label=self.update_resource_form_label),
            SaveResourceAndReturnAction(label=self.update_and_return_resource_form_label),
            ReturnToResourceIndexAction(label=self.cancel_resource_form_label),
        ]

    def create_index_view_class(self) -> type[View]:
        view = type(
            "{label}ResourceIndexView".format(label=self.label),
            (views.TableView,),
            dict(
                label=self.index_label.format(label=self.label, label_plural=self.label_plural),
                group=self.group,
                page_param=self.page_param,
                page_size_param=self.page_size_param,
                page_size=self.page_size,
                page_sizes=self.page_sizes,
                ordering_param=self.ordering_param,
                datasource=self.datasource,
                columns=self.columns,
                filters=self.page_filters,
                actions=self.get_index_page_actions(),
                metrics=self.page_metrics,
                row_actions=self.get_object_actions(),
                batch_actions=self.batch_actions,
                search_param=self.search_param,
                search_placeholder=self.search_placeholder,
                url_name=self.get_index_route_name(),
            ),
        )
        return typing.cast(type[View], view)

    def create_edit_view_class(self) -> type[View]:
        view = type(
            "{label}ResourceEditView".format(label=self.label),
            (views.FormView,),
            dict(
                label=self.edit_label.format(label=self.label, label_plural=self.label_plural),
                group=self.group,
                url_name=self.get_edit_route_name(),
                form_class=self.form_class,
                layout_class=self.form_layout_class,
                form_actions=self.get_edit_form_actions(),
                init_form=self.init_form,
                get_object=self.get_form_object,
                handle=self.perform_update,
            ),
        )
        return typing.cast(type[View], view)

    def create_create_view_class(self) -> type[View]:
        view = type(
            "{label}ResourceCreateView".format(label=self.label),
            (views.FormView,),
            dict(
                label=self.create_label.format(label=self.label, label_plural=self.label_plural),
                group=self.group,
                url_name=self.get_create_route_name(),
                form_class=self.create_form_class or self.form_class,
                layout_class=self.create_form_layout_class or self.form_layout_class,
                form_actions=self.get_create_form_actions(),
                init_form=self.init_create_form,
                get_object=self.get_new_object,
                handle=self.perform_create,
            ),
        )
        return typing.cast(type[View], view)

    def get_index_route_name(self) -> str:
        return "ohmyadmin.resource.{resource}.index".format(resource=self.slug)

    def get_create_route_name(self) -> str:
        return "ohmyadmin.resource.{resource}.create".format(resource=self.slug)

    def get_edit_route_name(self) -> str:
        return "ohmyadmin.resource.{resource}.edit".format(resource=self.slug)

    def get_delete_route_name(self) -> str:
        return "ohmyadmin.resource.{resource}.delete".format(resource=self.slug)

    def get_display_route_name(self) -> str:
        return "ohmyadmin.resource.{resource}.show".format(resource=self.slug)

    async def get_menu_item(self, request: Request) -> MenuItem:
        """Generate a menu item."""
        return MenuItem(label=self.label_plural, group=self.group, url=request.url_for(self.get_index_route_name()))

    def get_route(self) -> BaseRoute:
        return Mount(
            "/",
            routes=[
                Mount(
                    "/new",
                    routes=[
                        self.create_view.get_route(),
                    ],
                ),
                Mount(
                    "/{object_id}/edit",
                    routes=[
                        self.edit_view.get_route(),
                    ],
                ),
                self.index_view.get_route(),
            ],
            middleware=[Middleware(ExposeViewMiddleware, view=self, resource=self)],
        )

    async def init_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def init_create_form(self, request: Request, form: wtforms.Form) -> None:
        return await self.init_form(request, form)

    async def get_form_object(self, request: Request) -> typing.Any:
        object_id = request.path_params.get("object_id", "")
        pk_field = self.datasource.get_id_field()
        return await self.datasource.filter(InFilter(pk_field, [object_id])).one(request)

    def get_new_object(self, request: Request) -> typing.Any:
        return self.datasource.new()

    async def perform_create(self, request: Request, form: wtforms.Form, instance: object) -> Response:
        try:
            form.populate_obj(instance)
            await self.datasource.create(request, instance)
        except DuplicateError:
            message = _("Duplicate resource. There is another {label} like this already.", domain="ohmyadmin").format(
                label=self.label.lower(),
            )
            return htmx.response(409).toast(message, "error")

        toast_message = self.create_message.format(object=instance, label=self.label, label_plural=self.label_plural)
        response = htmx.response().toast(toast_message)

        form_data = await request.form()
        if SubmitActionType.SAVE_RETURN in form_data:
            return response.location(request.url_for(self.get_index_route_name()))

        pk = self.datasource.get_pk(instance)
        target_url = request.url_for(self.get_edit_route_name(), object_id=pk)
        return response.location(target_url)

    async def perform_update(self, request: Request, form: wtforms.Form, instance: object) -> Response:
        form.populate_obj(instance)
        await self.datasource.update(request, instance)

        toast_message = self.update_message.format(object=instance, label=self.label, label_plural=self.label_plural)
        response = htmx.response().toast(toast_message)

        form_data = await request.form()
        if SubmitActionType.SAVE_RETURN in form_data:
            return response.location(request.url_for(self.get_index_route_name()))

        pk = self.datasource.get_pk(instance)
        target_url = request.url_for(self.get_edit_route_name(), object_id=pk)
        return response.location(target_url)
