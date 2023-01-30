import dataclasses

import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from ohmyadmin import actions
from ohmyadmin.pages.form import FormPage
from ohmyadmin.testing import MarkupSelector
from tests.conftest import CreateTestAppFactory


class MyForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class MyPage(FormPage):  # pragma: no cover
    slug = 'myform'
    form_class = MyForm

    async def handle_submit(self, request: Request, form: MyForm, model: typing.Any) -> Response:
        return Response(f'SUBMITTED {form.name.data}')


async def test_renders_form(create_test_app: CreateTestAppFactory) -> None:
    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get('/admin/myform')
    selector = MarkupSelector(response.text)
    assert selector.has_node('form input[type="text"][name="name"]')


async def test_handles_form(create_test_app: CreateTestAppFactory) -> None:
    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.post('/admin/myform', data={'name': 'TEST'})
    assert response.text == 'SUBMITTED TEST'


async def test_renders_default_form_action(create_test_app: CreateTestAppFactory) -> None:
    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get('/admin/myform')
    selector = MarkupSelector(response.text)
    assert selector.get_text('form button[type="submit"]') == 'Submit'
    assert selector.has_class('form button[type="submit"]', 'btn-accent')


async def test_renders_custom_form_actions(create_test_app: CreateTestAppFactory) -> None:
    class MyPage(FormPage):
        slug = 'myform'
        form_class = MyForm
        form_actions = [actions.Submit('CUSTOM')]

        async def handle_submit(
            self, request: Request, form: wtforms.Form, model: typing.Any
        ) -> Response:  # pragma: no cover
            return Response('SUBMITTED')

    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get('/admin/myform')
    selector = MarkupSelector(response.text)
    assert selector.get_text('form button[type="submit"]') == 'CUSTOM'


async def test_populates_form_object(create_test_app: CreateTestAppFactory) -> None:
    @dataclasses.dataclass
    class Model:
        name: str

    class MyPage(FormPage):
        slug = 'myform'
        form_class = MyForm
        form_actions = [actions.Submit('CUSTOM')]

        async def get_form_object(self, request: Request) -> typing.Any:  # pragma: no cover
            return Model(name='TEST')

        async def handle_submit(
            self, request: Request, form: wtforms.Form, model: typing.Any
        ) -> Response:  # pragma: no cover
            return Response('SUBMITTED')

    app = create_test_app(pages=[MyPage()])
    client = TestClient(app)
    response = client.get('/admin/myform')
    selector = MarkupSelector(response.text)
    assert selector.get_attribute('form input[type="text"][name="name"]', 'value') == 'TEST'
