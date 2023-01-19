import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette_flash import flash

from ohmyadmin.pages.form import FormPage


class ProfileForm(wtforms.Form):
    first_name = wtforms.StringField()
    last_name = wtforms.StringField()


class ProfilePage(FormPage):
    icon = 'user'
    group = 'Settings'
    form_class = ProfileForm

    async def get_form_object(self, request: Request) -> typing.Any:
        return request.user

    async def handle_submit(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        form.populate_obj(model)
        await request.state.dbsession.commit()
        flash(request).success('Profile updated')
        return self.redirect_to_self(request)
