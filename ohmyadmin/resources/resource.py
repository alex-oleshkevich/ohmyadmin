import typing

import slugify
import wtforms
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin import filters, htmx, metrics, screens
from ohmyadmin.actions import actions
from ohmyadmin.breadcrumbs import Breadcrumb
from ohmyadmin.components import Component, FormLayoutBuilder
from ohmyadmin.components.display import DetailView
from ohmyadmin.components.form import FormView
from ohmyadmin.components.index import IndexView
from ohmyadmin.datasources.datasource import DataSource, DuplicateError, InFilter
from ohmyadmin.forms.utils import populate_object
from ohmyadmin.helpers import pluralize, snake_to_sentence
from ohmyadmin.resources.actions import (
    DeleteResourceAction,
    EditResourceAction,
    SubmitActionType,
)
from ohmyadmin.resources.policy import AccessPolicy, PermissiveAccessPolicy
from ohmyadmin.routing import LazyURL
from ohmyadmin.screens.base import ExposeViewMiddleware, Screen


class ResourceScreen(Screen):
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
    display_resource_label: str = _("View", domain="ohmyadmin")
    delete_resource_label: str = _("Edit", domain="ohmyadmin")
    create_resource_form_label: str = _("Create")
    create_and_return_resource_form_label: str = _("Create and return to list")
    update_resource_form_label: str = _("Update")
    update_and_return_resource_form_label: str = _("Update and return to list")
    cancel_resource_form_label: str = _("Cancel")

    # permissions
    access_policy: AccessPolicy = PermissiveAccessPolicy()

    # data
    datasource: typing.ClassVar[DataSource | None] = None

    # actions
    action_classes: typing.Sequence[type[actions.NewAction]] = tuple()

    # index page
    index_view_class: IndexView = IndexView
    page_param: typing.ClassVar[str] = "page"
    page_size_param: typing.ClassVar[str] = "page_size"
    page_size: typing.ClassVar[int] = 25
    page_sizes: typing.ClassVar[typing.Sequence[int]] = [10, 25, 50, 100]

    ordering_param: typing.ClassVar[str] = "ordering"
    ordering_fields: typing.Sequence[str] = tuple()
    ordering_filter: filters.Filter | None = None

    page_filters: typing.Sequence[filters.Filter] = tuple()
    page_actions: typing.Sequence[Component] = tuple()
    page_metrics: typing.Sequence[metrics.Metric] = tuple()
    object_actions: typing.Sequence[actions.Action] = tuple()
    batch_actions: typing.Sequence[actions.ModalAction] = tuple()

    search_param: str = "search"
    search_placeholder: str = _("Start typing to search...")
    searchable_fields: typing.Sequence[str] = tuple()
    search_filter: filters.Filter | None = None

    # edit page
    form_class: type[wtforms.Form] = wtforms.Form
    form_view_class: type[FormView] = FormView
    form_actions: typing.Sequence[actions.Action] = tuple()

    # create page
    create_form_class: type[wtforms.Form] | None = None
    create_form_view_class: type[FormLayoutBuilder] | None = None
    create_form_actions: typing.Sequence[actions.Action] | None = None

    # display page
    display_object_actions: typing.Sequence[actions.Action] = tuple()
    detail_view_class: type[DetailView] = DetailView

    def __init__(self) -> None:
        assert self.datasource, f"Class {self.__class__.__name__} must have a datasource."
        self.label = self.label or snake_to_sentence(self.__class__.__name__.removesuffix("Resource"))
        self.label_plural = self.label_plural or pluralize(self.label)
        self.index_screen = self.create_index_screen_class()()
        self.edit_screen = self.create_edit_screen_class()()
        self.create_screen = self.create_create_screen_class()()
        self.display_screen = self.create_display_screen_class()()

    @property
    def slug(self) -> str:
        return slugify.slugify(self.label_plural)

    @classmethod
    @property
    def url_name(cls) -> str:
        slug = slugify.slugify(".".join([cls.__module__, cls.__name__]))
        return f"ohmyadmin.resource.{slug}"

    def get_index_page_actions(self) -> list[actions.Action]:
        """Return user defined actions along with default actions."""
        return [
            # *self.page_actions,
            # CreateResourceAction(
            #     label=self.create_resource_label.format(label=self.label, label_plural=self.label_plural),
            # ),
        ]

    def get_batch_actions(self) -> list[actions.Action]:
        return [
            # *self.batch_actions,
            # DeleteResourceAction(),
        ]

    def get_create_form_actions(self) -> list[actions.Action]:
        return (
            self.create_form_actions
            or [
                # SaveResourceAction(label=self.create_resource_form_label),
                # SaveResourceAndReturnAction(label=self.create_and_return_resource_form_label),
                # ReturnToResourceIndexAction(label=self.cancel_resource_form_label),
            ]
        )

    def get_edit_form_actions(self) -> list[actions.Action]:
        return (
            self.form_actions
            or [
                # SaveResourceAction(label=self.update_resource_form_label),
                # SaveResourceAndReturnAction(label=self.update_and_return_resource_form_label),
                # ReturnToResourceIndexAction(label=self.cancel_resource_form_label),
            ]
        )

    def get_display_actions(self) -> list[actions.Action]:
        return [*self.display_object_actions, EditResourceAction(), DeleteResourceAction()]

    def create_index_screen_class(self) -> type[Screen]:
        screen = type(
            "{label}ResourceIndexScreen".format(label=self.label),
            (screens.IndexScreen,),
            dict(
                label=self.index_label.format(label=self.label, label_plural=self.label_plural),
                group=self.group,
                page_param=self.page_param,
                page_size_param=self.page_size_param,
                page_size=self.page_size,
                page_sizes=self.page_sizes,
                ordering_param=self.ordering_param,
                ordering_fields=self.ordering_fields,
                ordering_filter=self.ordering_filter,
                datasource=self.datasource,
                filters=self.page_filters,
                page_actions=self.get_index_page_actions(),
                page_metrics=self.page_metrics,
                batch_actions=self.get_batch_actions(),
                search_param=self.search_param,
                search_placeholder=self.search_placeholder,
                searchable_fields=self.searchable_fields,
                search_filter=self.search_filter,
                url_name=self.get_index_route_name(),
                view_class=self.index_view_class,
                page_toolbar=self.page_toolbar,
                breadcrumbs=[
                    Breadcrumb(label=_("Home", domain="ohmyadmin"), url=lambda r: r.url_for("ohmyadmin.welcome")),
                    Breadcrumb(label=self.label_plural, url=lambda r: r.url_for(self.get_index_route_name())),
                ],
            ),
        )
        return typing.cast(type[Screen], screen)

    def create_edit_screen_class(self) -> type[Screen]:
        screen = type(
            "{label}ResourceEditScreen".format(label=self.label),
            (screens.FormScreen,),
            dict(
                label=self.edit_label.format(label=self.label, label_plural=self.label_plural),
                group=self.group,
                url_name=self.get_edit_route_name(),
                form_class=self.form_class,
                layout_class=self.form_view_class,
                form_actions=self.get_edit_form_actions(),
                init_form=self.init_form,
                get_object=self.get_object_for_form,
                handle=self.perform_update,
                breadcrumbs=[
                    Breadcrumb(label=_("Home", domain="ohmyadmin"), url=lambda r: r.url_for("ohmyadmin.welcome")),
                    Breadcrumb(label=self.label_plural, url=lambda r: r.url_for(self.get_index_route_name())),
                    Breadcrumb(label=_("Edit", domain="ohmyadmin")),
                ],
            ),
        )
        return typing.cast(type[Screen], screen)

    def create_create_screen_class(self) -> type[Screen]:
        screen = type(
            "{label}ResourceCreateScreen".format(label=self.label),
            (screens.FormScreen,),
            dict(
                label=self.create_label.format(label=self.label, label_plural=self.label_plural),
                group=self.group,
                url_name=self.get_create_route_name(),
                form_class=self.create_form_class or self.form_class,
                layout_class=self.create_form_view_class or self.form_view_class,
                form_actions=self.get_create_form_actions(),
                init_form=self.init_create_form,
                get_object=self.get_new_object,
                handle=self.perform_create,
                breadcrumbs=[
                    Breadcrumb(label=_("Home", domain="ohmyadmin"), url=lambda r: r.url_for("ohmyadmin.welcome")),
                    Breadcrumb(label=self.label_plural, url=lambda r: r.url_for(self.get_index_route_name())),
                    Breadcrumb(label=_("Create", domain="ohmyadmin")),
                ],
            ),
        )
        return typing.cast(type[Screen], screen)

    def create_display_screen_class(self) -> type[Screen]:
        screen = type(
            "{label}ResourceDisplayScreen".format(label=self.label),
            (screens.DisplayScreen,),
            dict(
                label=self.display_label.format(label=self.label, label_plural=self.label_plural),
                group=self.group,
                url_name=self.get_display_route_name(),
                page_actions=self.get_display_actions(),
                get_object=self.get_object_for_display,
                view_class=self.detail_view_class,
                breadcrumbs=[
                    Breadcrumb(label=_("Home", domain="ohmyadmin"), url=lambda r: r.url_for("ohmyadmin.welcome")),
                    Breadcrumb(label=self.label_plural, url=lambda r: r.url_for(self.get_index_route_name())),
                    Breadcrumb(label=_("View", domain="ohmyadmin")),
                ],
            ),
        )
        return typing.cast(type[Screen], screen)

    @classmethod
    def get_index_route_name(cls) -> str:
        return cls.url_name

    @classmethod
    def get_index_page_route(cls) -> LazyURL:
        return LazyURL(cls.get_index_route_name())

    @classmethod
    def get_create_route_name(cls) -> str:
        return "{url_name}.create".format(url_name=cls.url_name)

    @classmethod
    def get_create_page_route(cls) -> LazyURL:
        return LazyURL(cls.get_create_route_name())

    @classmethod
    def get_edit_route_name(cls) -> str:
        return "{url_name}.edit".format(url_name=cls.url_name)

    @classmethod
    def get_edit_page_route(cls, object_id: int) -> LazyURL:
        return LazyURL(cls.get_edit_route_name(), path_params=dict(object_id=object_id))

    @classmethod
    def get_display_route_name(cls) -> str:
        return "{url_name}.show".format(url_name=cls.url_name)

    @classmethod
    def get_display_page_route(cls, object_id: int) -> LazyURL:
        return LazyURL(cls.get_display_route_name(), path_params=dict(object_id=object_id))

    @classmethod
    def get_action_route(
        cls, action: type[actions.NewAction], object_ids: typing.Sequence[str] | None = None
    ) -> LazyURL:
        object_ids = object_ids or []
        return LazyURL(
            "ohmyadmin.resource.action",
            query_params={"object_id": object_ids},
            path_params=dict(action_id=action.url_name),
        )

    def get_action_classes(self) -> list[type[actions.NewAction]]:
        return self.action_classes or []

    def get_action_class(self, action_id: str) -> type[actions.NewAction]:
        for action in self.get_action_classes():
            if action.url_name == action_id:
                return action
        raise ValueError(f'Action "{action_id}" does not exist.')

    def get_route(self) -> BaseRoute:
        return Mount(
            "/",
            routes=[
                Mount(
                    "/new",
                    routes=[
                        self.create_screen.get_route(),
                    ],
                ),
                Mount(
                    "/{object_id}/edit",
                    routes=[
                        self.edit_screen.get_route(),
                    ],
                ),
                Mount(
                    "/{object_id}/view",
                    routes=[
                        self.display_screen.get_route(),
                    ],
                ),
                Route(
                    "/actions/{action_id}", self.action_view, name="ohmyadmin.resource.action", methods=["get", "post"]
                ),
                self.index_screen.get_route(),
            ],
            middleware=[Middleware(ExposeViewMiddleware, screen=self, resource=self)],
        )

    async def list_view(self, request: Request) -> Response:
        ...

    async def create_view(self, request: Request) -> Response:
        ...

    async def edit_view(self, request: Request) -> Response:
        ...

    async def delete_view(self, request: Request) -> Response:
        ...

    async def action_view(self, request: Request) -> Response:
        action_id = request.path_params["action_id"]
        action_class = self.get_action_class(action_id)
        action = action_class()
        object_ids = request.query_params.getlist("object_id")
        return await action.dispatch(request, object_ids)

    async def init_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def init_create_form(self, request: Request, form: wtforms.Form) -> None:
        return await self.init_form(request, form)

    async def get_object_for_form(self, request: Request) -> typing.Any:
        object_id = request.path_params.get("object_id", "")
        pk_field = self.datasource.get_id_field()
        return await self.datasource.filter(InFilter(pk_field, [object_id])).one(request)

    async def get_object_for_display(self, request: Request) -> typing.Any:
        object_id = request.path_params.get("object_id", "")
        pk_field = self.datasource.get_id_field()
        return await self.datasource.filter(InFilter(pk_field, [object_id])).one(request)

    def get_new_object(self, request: Request) -> typing.Any:
        return self.datasource.new()

    async def populate_object(self, request: Request, form: wtforms.Form, model: object) -> None:
        await populate_object(request, form, model)

    async def perform_create(self, request: Request, form: wtforms.Form, model: object) -> Response:
        try:
            await self.populate_object(request, form, model)
            await self.datasource.create(request, model)
        except DuplicateError:
            message = _("Duplicate resource. There is another {label} like this already.", domain="ohmyadmin").format(
                label=self.label.lower(),
            )
            return htmx.response(409).toast(message, "error")

        toast_message = self.create_message.format(object=model, label=self.label, label_plural=self.label_plural)
        response = htmx.response().toast(toast_message)

        form_data = await request.form()
        if SubmitActionType.SAVE_RETURN in form_data:
            return response.location(request.url_for(self.get_index_route_name()))

        pk = self.datasource.get_pk(model)
        target_url = request.url_for(self.get_edit_route_name(), object_id=pk)
        return response.location(target_url)

    async def perform_update(self, request: Request, form: wtforms.Form, model: object) -> Response:
        await self.populate_object(request, form, model)
        await self.datasource.update(request, model)

        toast_message = self.update_message.format(object=model, label=self.label, label_plural=self.label_plural)
        response = htmx.response()

        form_data = await request.form()
        if SubmitActionType.SAVE_RETURN in form_data:
            flash(request).success(toast_message)
            return response.location(request.url_for(self.get_index_route_name()), {"select": "#datatable"})

        return response.toast(toast_message)

    async def sync_for_to_model(self, request: Request, form: wtforms.Form, model: object) -> None:
        await populate_object(request, form, model)
