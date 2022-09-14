import sqlalchemy as sa

from examples.models import User
from ohmyadmin.forms import CheckboxField, EmailField, FileField, Form, HiddenField, TextField
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BoolColumn, Column, ImageColumn


class EditForm(Form):
    first_name = TextField()
    last_name = TextField()
    photo = FileField(upload_to='photos')
    email = EmailField(required=True)
    is_active = CheckboxField(default=True)
    password = HiddenField(default='')


class UserResource(Resource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    entity_class = User
    form_class = EditForm
    queryset = sa.select(entity_class).order_by(User.id)
    table_columns = [
        Column('id', label='ID'),
        ImageColumn('photo', url_prefix='/media/'),
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
        BoolColumn('is_active', label='Active'),
    ]
