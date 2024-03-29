from __future__ import annotations
import wtforms
from starlette.requests import Request

from examples import icons
from examples.models import Country
from ohmyadmin import components
from ohmyadmin.components import ButtonVariant, CellAlign, Component
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.actions import DeleteResourceAction
from ohmyadmin.resources.resource import ResourceScreen


class CountryForm(wtforms.Form):
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CountryDetailView(components.DetailView[Country]):
    def compose(self, request: Request) -> components.Component:
        return components.Column(
            [
                components.ModelField("Code", components.Text(self.model.code)),
                components.ModelField("Name", components.Text(self.model.name)),
            ]
        )


class FormView(components.FormView[CountryForm, Country]):
    def compose(self, request: Request) -> Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=6,
                    children=[
                        components.FormInput(self.form.code),
                        components.FormInput(self.form.name),
                    ],
                )
            ]
        )


class CountryIndexView(components.IndexView[Country]):
    def compose(self, request: Request) -> components.Component:
        return components.Table(
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableSortableHeadCell("Code", sort_field="code"),
                    components.TableHeadCell("Name"),
                    components.TableHeadCell("Actions", align=CellAlign.RIGHT),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        child=components.Link(
                            text=str(row),
                            url=CountryResource.get_edit_page_route(row.code),
                        ),
                    ),
                    components.TableColumn(components.Text(row.name)),
                    components.TableColumn(
                        components.Row(
                            children=[
                                components.DropdownMenu(
                                    trigger=components.Button(
                                        icon=icons.ICON_DOTS,
                                        variant=components.ButtonVariant.TEXT,
                                    ),
                                    items=[
                                        components.DropdownMenuLink(
                                            url=CountryResource.get_display_page_route(row.code),
                                            child=components.Text("View"),
                                            leading=components.HTML(icons.ICON_EYE),
                                        ),
                                        components.DropdownMenuLink(
                                            url=CountryResource.get_edit_page_route(row.code),
                                            child=components.Text("Edit"),
                                            leading=components.HTML(icons.ICON_PENCIL),
                                        ),
                                        components.DropdownMenuModal(DeleteResourceAction, object_ids=[row.code]),
                                    ],
                                ),
                            ]
                        ),
                        align=CellAlign.RIGHT,
                    ),
                ]
            ),
        )


class CountryResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_COUNTRIES
    datasource = SADataSource(Country)
    form_class = CountryForm
    index_view_class = CountryIndexView
    detail_view_class = CountryDetailView
    form_view_class = FormView
    ordering_fields = ("code",)
    action_classes = (DeleteResourceAction,)
    page_toolbar = components.PageToolbar(
        builder=lambda _: [
            components.LinkButton(
                url=CountryResource.get_create_page_route(),
                text="Add country",
                icon=icons.ICON_PLUS,
                variant=ButtonVariant.ACCENT,
            )
        ]
    )

