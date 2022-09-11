import sqlalchemy as sa
from starlette.requests import Request

from examples.models import User
from ohmyadmin.actions import LinkAction
from ohmyadmin.flash import flash
from ohmyadmin.forms import CheckboxField, EmailField, HiddenField, TextField
from ohmyadmin.resources import Resource
from ohmyadmin.responses import RedirectResponse, Response
from ohmyadmin.tables import ActionGroup, BatchAction, Column, LinkRowAction


class DeleteAllAction(BatchAction):
    id = 'delete'
    label = 'Delete all'
    dangerous = True
    confirmation = 'Do you want to delete all items?'
    fields = [
        TextField('name'),
        TextField('email'),
    ]

    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        flash(request).success('Object has been removed')
        return RedirectResponse(request).to_resource(request.state.resource)


class DeactivateAllAction(BatchAction):
    id = 'deactivate'
    label = 'Deactivate all'
    confirmation = 'Do you want to run this action?'

    async def apply(self, request: Request, queryset: sa.sql.Select, params: dict[str, str]) -> Response:
        return RedirectResponse(request).to_resource(request.state.resource)


class ActivateAllAction(BatchAction):
    id = 'activate'
    label = 'Activate all'
    confirmation = 'Do you want to run this action?'

    async def apply(self, request: Request, queryset: sa.sql.Select, params: dict[str, str]) -> Response:
        return RedirectResponse(request).to_resource(request.state.resource)


class UserResource(Resource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    entity_class = User
    queryset = sa.select(entity_class).order_by(User.id)
    table_columns = [
        Column('id', label='ID'),
        Column(
            'full_name',
            label='Name',
            sortable=True,
            searchable=True,
            search_in=['first_name', 'last_name'],
            sort_by='last_name',
            link=True,
        ),
        Column('email', label='Email', searchable=True),
        Column('is_active', label='Active'),
    ]
    edit_form = [
        TextField('first_name'),
        TextField('last_name'),
        EmailField('email', required=True),
        CheckboxField('is_active', default=True),
        HiddenField('password', default=''),
    ]
    row_actions = [
        ActionGroup(
            [
                LinkRowAction(lambda o: '/admin/resources/users/', 'Impersonate'),
                LinkRowAction(lambda o: '/admin/resources/users/', 'Deactivate'),
                LinkRowAction(lambda o: '/admin/resources/users/', 'Preview'),
                LinkRowAction(lambda o: '/admin/resources/users/', 'Export as CSV'),
                LinkRowAction(lambda o: '/admin/resources/users/', 'Transfer License'),
                LinkRowAction(lambda o: f'/admin/resources/users/view/{o.id}', 'View', icon='eye'),
                LinkRowAction(lambda o: f'/admin/resources/delete/view/{o.id}', 'Delete', icon='trash', color='danger'),
            ]
        ),
    ]
    batch_actions = [
        DeleteAllAction(),
        ActivateAllAction(),
        DeactivateAllAction(),
    ]
    table_actions = [
        LinkAction('/admin', 'Export', icon='download'),
    ]
