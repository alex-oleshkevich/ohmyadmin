import datetime
import decimal
from starlette_babel import gettext_lazy as _
import sqlalchemy as sa
import wtforms
from markupsafe import Markup
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin import colors, formatters
from ohmyadmin.actions import actions
from ohmyadmin.breadcrumbs import Breadcrumb
from ohmyadmin.datasources.datasource import InFilter
from ohmyadmin.datasources.sqlalchemy import get_dbsession, SADataSource
from ohmyadmin.filters import (
    ChoiceFilter,
    DateFilter,
    DateRangeFilter,
    DateTimeFilter,
    DateTimeRangeFilter,
    DecimalFilter,
    FloatFilter,
    IntegerFilter,
    MultiChoiceFilter,
    StringFilter,
)
from ohmyadmin.formatters import (
    AvatarFormatter,
    BoolFormatter,
    CallbackFormatter,
    DateFormatter,
    LinkFormatter,
    NumberFormatter,
)
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.htmx import response
from ohmyadmin.metrics.partition import Partition, PartitionMetric
from ohmyadmin.metrics.progress import ProgressMetric
from ohmyadmin.metrics.trend import TrendMetric, TrendValue
from ohmyadmin.metrics.value import ValueMetric, ValueValue
from ohmyadmin.screens.table import TableScreen
from ohmyadmin.display_fields import DisplayField


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


async def object_toast_callback(request: Request) -> Response:
    view: TableScreen = request.state.screen
    query = view.get_query(request).filter(InFilter("id", request.query_params.get("object_id")))
    count = await query.count(request)
    return response().toast(f"Object selected: {count}.").close_modal()


class RowObjectForm(wtforms.Form):
    first_name = wtforms.StringField()
    last_name = wtforms.StringField(validators=[wtforms.validators.data_required()])


async def object_form_callback(request: Request, form: wtforms.Form) -> Response:
    print(form.data)
    return response().toast("Form submitted").close_modal().refresh()


async def delete_selected_callback(request: Request, form: wtforms.Form) -> Response:
    print(form.data)
    view: TableScreen = request.state.view
    query = view.get_query(request)
    query = await view.apply_filters(request, query)
    if "__all__" not in request.query_params:
        query = query.filter(InFilter("id", request.query_params.getlist("object_id")))
    count = await query.count(request)
    return response().toast(f"Rows deleted: {count}.").close_modal().refresh()


class GenderDistributionMetric(PartitionMetric):
    label = "Gender distribution"

    async def calculate(self, request: Request) -> list[Partition]:
        stmt = sa.select(User.gender, sa.func.count("*").label("count")).group_by(User.gender)
        result = await get_dbsession(request).execute(stmt)
        rows = result.all()
        return [Partition(label=row.gender, value=row.count) for row in rows]


class AdultsMetric(ValueMetric):
    label = "Adults"
    size = 2
    formatter = formatters.NumberFormatter(suffix=" users")

    async def calculate(self, request: Request) -> ValueValue:
        stmt = (
            sa.select(sa.func.count("*").label("count"))
            .select_from(User)
            .where(sa.func.age(User.birthdate) > sa.text("interval '18 years'"))
        )
        result = await get_dbsession(request).execute(stmt)
        return result.scalars().one()


class RegistrationsByYearMetric(TrendMetric):
    label = "Registrations by year"
    size = 4
    show_current_value = True
    update_interval = 2
    formatter = formatters.StringFormatter(suffix=" new users")

    async def calculate_current_value(self, request: Request) -> int | float | decimal.Decimal:
        stmt = sa.select(sa.func.count("*")).where(
            User.created_at >= datetime.datetime.now() - datetime.timedelta(days=10 * 365)
        )
        result = await get_dbsession(request).execute(stmt)
        return result.scalars().one()

    async def calculate(self, request: Request) -> list[TrendValue]:
        stmt = (
            sa.select(sa.func.count("*").label("count"), sa.func.date_trunc("year", User.created_at).label("date"))
            .group_by(sa.text("2"))
            .order_by(sa.text("2"))
            .where(User.created_at >= datetime.datetime.now() - datetime.timedelta(days=10 * 365))
        )
        result = await get_dbsession(request).execute(stmt)
        return [TrendValue(label=str(row.date.year), value=row.count) for row in result.all()]


class ActivationProgressMetric(ProgressMetric):
    label = "Activation Progress"
    color = colors.COLOR_EMERALD

    async def calculate(self, request: Request) -> int | float:
        stmt = sa.select(sa.func.count("*")).where(User.is_active == True)  # noqa: E712
        result = await get_dbsession(request).execute(stmt)
        return result.scalars().one()

    async def calculate_target(self, request: Request) -> int | float:
        stmt = sa.select(sa.func.count("*")).select_from(User)
        result = await get_dbsession(request).execute(stmt)
        return result.scalars().one()


class UsersTable(TableScreen):
    label = "Table view"
    group = "Views"
    description = "Demo of table view."
    datasource = SADataSource(User)
    searchable_fields = ["last_name", "email"]
    ordering_fields = "last_name", "email", "rating", "birthdate", "created_at"
    breadcrumbs = [
        Breadcrumb(_("Home"), url="/admin"),
        Breadcrumb(label),
    ]
    page_metrics = (
        GenderDistributionMetric(),
        RegistrationsByYearMetric(),
        ActivationProgressMetric(),
        AdultsMetric(),
    )
    filters = [
        StringFilter("last_name"),
        StringFilter("email"),
        IntegerFilter("id", label="ID"),
        FloatFilter("rating", label="Rating from"),
        FloatFilter("rating", label="Rating to", filter_id="rating_to"),
        DecimalFilter("balance"),
        DateFilter("birthdate"),
        DateTimeFilter("created_at"),
        DateRangeFilter("created_at", filter_id="created_range"),
        DateTimeRangeFilter("created_at", filter_id="created_timerange"),
        ChoiceFilter(
            "gender",
            choices=[
                ("male", "Male"),
                ("female", "Female"),
                ("unknown", "Unknown"),
            ],
        ),
        MultiChoiceFilter(
            "gender",
            filter_id="gender_multi",
            choices=[
                ("male", "Male"),
                ("female", "Female"),
                ("unknown", "Unknown"),
            ],
        ),
    ]
    batch_actions = [
        actions.ModalAction(label="Delete selected row", dangerous=True, callback=delete_selected_callback),
        actions.ModalAction(
            label="Batch Update",
            callback=object_form_callback,
            form_class=RowObjectForm,
            icon=PLUS_ICON,
        ),
    ]
    object_actions = [
        actions.LinkAction(url="/admin", label="Show details"),
        actions.CallbackAction(label="Show toast", callback=object_toast_callback),
        actions.CallbackAction(
            dangerous=True,
            label="Show toast with confirmation",
            callback=object_toast_callback,
            confirmation="Call this dangerous action?",
        ),
        actions.ModalAction(
            label="Form action",
            callback=object_form_callback,
            form_class=RowObjectForm,
            icon=PLUS_ICON,
        ),
        actions.ModalAction(
            label="Dangerous form action",
            dangerous=True,
            callback=object_form_callback,
            form_class=RowObjectForm,
            icon=PLUS_ICON,
        ),
    ]
    page_actions = [
        actions.LinkAction(url="/admin", label="To Main page"),
        actions.CallbackAction("Show toast", callback=show_toast_callback),
        actions.ModalAction(
            icon=PLUS_ICON,
            label="New User",
            variant="accent",
            modal_title="Create user",
            form_class=CreateUserForm,
            callback=create_user_callback,
            modal_description="Create a new user right now!",
        ),
    ]

    columns = [
        DisplayField("photo", formatter=AvatarFormatter()),
        DisplayField("first_name", formatter=LinkFormatter(url="/admin")),
        DisplayField("last_name"),
        DisplayField("birthdate", formatter=DateFormatter()),
        DisplayField("balance", formatter=NumberFormatter(prefix="$", align="right")),
        DisplayField("rating"),
        DisplayField("email"),
        DisplayField("is_active", formatter=BoolFormatter(as_text=True)),
        DisplayField("gender", formatter=CallbackFormatter(lambda r, v: snake_to_sentence(v))),
        DisplayField("created_at", formatter=DateFormatter()),
    ]
