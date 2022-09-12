import sqlalchemy as sa

from examples.models import User
from ohmyadmin.forms import CheckboxField, EmailField, FileField, HiddenField, TextField
from ohmyadmin.resources import Resource
from ohmyadmin.tables import Column, ImageColumn


class UserResource(Resource):
    icon = 'users'
    label = 'User'
    label_plural = 'Users'
    entity_class = User
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
        Column('is_active', label='Active'),
    ]
    form_fields = [
        TextField('first_name'),
        TextField('last_name'),
        FileField('photo', upload_to='photos'),
        EmailField('email', required=True),
        CheckboxField('is_active', default=True),
        HiddenField('password', default=''),
    ]
