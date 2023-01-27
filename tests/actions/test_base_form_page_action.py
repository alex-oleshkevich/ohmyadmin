import typing
import wtforms
from starlette.requests import Request
from starlette.responses import Response
from unittest import mock

from ohmyadmin.actions import BaseFormPageAction, Submit
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory


class MyForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class MyAction(BaseFormPageAction):  # pragma: no cover
    form_class = MyForm

    async def handle(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        return Response('CALLED')


def test_generates_slug(http_request: Request) -> None:
    action = MyAction()
    assert action.slug == 'myaction'


async def test_loads_form_object(request_f: RequestFactory) -> None:
    request = request_f(method='get')
    action = MyAction()
    with mock.patch.object(action, 'get_form_object') as fn:
        await action.dispatch(request)
    fn.assert_awaited_once_with(request)


async def test_renders_form(request_f: RequestFactory) -> None:
    request = request_f(method='get')
    action = MyAction()
    response = await action.dispatch(request)
    selector = MarkupSelector(response.body)
    assert selector.has_node('form input[type="text"][name="name"]')
    assert selector.get_text('form button[type="submit"]') == 'Submit'
    assert selector.get_text('form button[type="button"].btn-text') == 'Cancel'


async def test_renders_form_with_actions(request_f: RequestFactory) -> None:
    request = request_f(method='get')
    action = MyAction()
    action.actions = [Submit(label='My Submit')]
    response = await action.dispatch(request)
    selector = MarkupSelector(response.body)
    assert selector.get_text('form button[type="submit"]') == 'My Submit'


async def test_submit_valid_form(request_f: RequestFactory) -> None:
    request = request_f(method='POST', form_data={'name': 'user'})
    action = MyAction()
    response = await action.dispatch(request)
    assert response.body == b'CALLED'
