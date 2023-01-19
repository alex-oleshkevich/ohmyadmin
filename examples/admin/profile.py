import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.models import User
from ohmyadmin.actions import ActionResponse
from ohmyadmin.pages.form import FormPage


class ProfileForm(wtforms.Form):
    first_name = wtforms.StringField()
    last_name = wtforms.StringField()


class ProfilePage(FormPage):
    icon = 'user'
    group = 'Settings'
    form_class = ProfileForm

    async def get_form_object(self, request: Request) -> typing.Any:
        return await request.state.dbsession.get(User, int(request.user.id))

    async def handle_submit(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        form.populate_obj(model)
        await request.state.dbsession.commit()
        return ActionResponse().show_toast('Profile updated')
