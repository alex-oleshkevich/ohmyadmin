import wtforms
from markupsafe import Markup
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin.actions import actions, object_actions
from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.filters import StringFilter
from ohmyadmin.formatters import (
    AvatarFormatter,
    BoolFormatter,
    DateFormatter,
    LinkFormatter,
)
from ohmyadmin.htmx import response
from ohmyadmin.views.table import Column, TableView


def user_edit_url(request: Request) -> URL:
    return UsersTable.get_url(request)


async def show_toast_callback(request: Request) -> Response:
    return response().toast("Clicked!")


class CreateUserForm(wtforms.Form):
    first_name = wtforms.StringField()
    last_name = wtforms.StringField()
    email = wtforms.EmailField(validators=[wtforms.validators.data_required()])
    password = wtforms.PasswordField(validators=[wtforms.validators.data_required()])
    confirm_password = wtforms.PasswordField(validators=[wtforms.validators.equal_to("password")])


PLUS_ICON = Markup(
    """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
<path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 5l0 14" />
<path d="M5 12l14 0" />
</svg>
"""
)


async def create_user_callback(request: Request, form: CreateUserForm) -> Response:
    print(form.data)
    return response().toast("New user created!").close_modal()


async def object_toast_callback(request: Request, query: DataSource) -> Response:
    return response().toast(f"Object selected: {query}.").close_modal()


class RowObjectForm(wtforms.Form):
    first_name = wtforms.StringField()
    last_name = wtforms.StringField(validators=[wtforms.validators.data_required()])


async def object_form_callback(request: Request, query: DataSource, form: wtforms.Form) -> Response:
    print(form.data)
    return response().toast(f"Form submitted: {query}.").close_modal().refresh()


async def delete_selected_callback(request: Request, query: DataSource, form: wtforms.Form) -> Response:
    print(form.data)
    count = await query.count(request)
    return response().toast(f"Rows deleted: {count}.").close_modal().refresh()


class UsersTable(TableView):
    label = "Users table"
    group = "Demos"
    description = "List all users."
    datasource = SADataSource(User)
    filters = [
        StringFilter("last_name"),
        StringFilter("email"),
        # IntegerFilter('id'),
    ]
    actions = [
        actions.LinkAction(url="/admin", label="To Main page"),
        actions.CallFunctionAction(function="alert", args=["kek"], label="Show alert"),
        actions.EventAction(event="refresh", variant="text", label="Refresh data"),
        actions.CallbackAction(show_toast_callback, label="Show toast", variant="danger"),
        actions.FormAction(
            icon=PLUS_ICON,
            label="New User",
            variant="accent",
            modal_title="Create user",
            form_class=CreateUserForm,
            callback=create_user_callback,
            modal_description="Create a new user right now!",
        ),
    ]
    row_actions = [
        object_actions.LinkAction(url="/admin", label="Show details"),
        object_actions.LinkAction(url=lambda r, o: f"/admin?id={o.id}", label="Generated URL"),
        object_actions.CallbackAction(label="Show toast", callback=object_toast_callback),
        object_actions.CallbackAction(
            dangerous=True,
            label="Show toast with confirmation",
            callback=object_toast_callback,
            confirmation="Call this dangerous action?",
        ),
        object_actions.FormAction(
            label="Form action",
            callback=object_form_callback,
            form_class=RowObjectForm,
            icon=PLUS_ICON,
        ),
        object_actions.FormAction(
            label="Dangerous form action",
            dangerous=True,
            callback=object_form_callback,
            form_class=RowObjectForm,
            icon=PLUS_ICON,
        ),
    ]
    batch_actions = [
        object_actions.BatchAction(label="Delete selected row", dangerous=True, callback=delete_selected_callback),
        object_actions.BatchAction(
            label="Batch Update",
            callback=object_form_callback,
            form_class=RowObjectForm,
            icon=PLUS_ICON,
        ),
    ]
    columns = [
        Column("photo", formatter=AvatarFormatter()),
        Column("first_name", formatter=LinkFormatter(url="/admin")),
        Column("last_name", searchable=True, sortable=True),
        Column("email", searchable=True),
        Column("is_active", sortable=True, formatter=BoolFormatter(as_text=True)),
        Column("created_at", sortable=True, formatter=DateFormatter()),
    ]
