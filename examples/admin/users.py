import sqlalchemy as sa
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from examples.models import User
from ohmyadmin.actions import LinkAction, SubmitAction
from ohmyadmin.forms import CheckboxField, EmailField, TextField
from ohmyadmin.resources import Resource
from ohmyadmin.tables import ActionGroup, BatchAction, Column, LinkRowAction


class DeleteAllAction(BatchAction):
    id = 'delete'
    label = 'Delete all'
    dangerous = True
    confirmation = 'Do you want to delete all items?'

    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        return RedirectResponse(request.headers.get('referer'), 302)


class DeactivateAllAction(BatchAction):
    id = 'deactivate'
    label = 'Deactivate all'
    dangerous = True
    confirmation = 'Do you want to run this action?'

    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        return RedirectResponse(request.headers.get('referer'), 302)


class ActivateAllAction(BatchAction):
    id = 'activate'
    label = 'Activate all'
    dangerous = True
    confirmation = 'Do you want to run this action?'

    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        return RedirectResponse(request.headers.get('referer'), 302)


class UserResource(Resource):
    label = 'User'
    label_plural = 'Users'
    queryset = sa.select(User)
    table_columns = [
        Column('id', label='ID'),
        Column(
            'full_name',
            label='Name',
            sortable=True,
            searchable=True,
            search_in=['first_name', 'last_name'],
            sort_by='last_name',
        ),
        Column('email', label='Email', searchable=True),
        Column('is_active', label='Active'),
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
        ActivateAllAction(),
        DeactivateAllAction(),
    ]
    table_actions = [
        LinkAction('/admin', 'Export', icon='download'),
    ]
    edit_form = [
        TextField('first_name'),
        TextField('last_name'),
        EmailField('email', required=True),
        CheckboxField('is_active', default=True),
    ]
    form_actions = [
        SubmitAction('Save', color='primary'),
        SubmitAction('Save and return to list'),
        SubmitAction('Save and create new'),
    ]