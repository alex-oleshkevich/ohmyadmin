import wtforms
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.actions import BaseBatchAction
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory


class MyForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class MyAction(BaseBatchAction):  # pragma: no cover
    form_class = MyForm

    async def apply(
        self, request: Request, object_ids: list[str], form: wtforms.Form
    ) -> Response:
        return Response("CALLED")


def test_generates_slug(http_request: Request) -> None:
    action = MyAction()
    assert action.slug == "myaction"


async def test_renders_form(request_f: RequestFactory) -> None:
    request = request_f(method="get", query_string="_ids=1")
    action = MyAction()
    response = await action.dispatch(request)
    selector = MarkupSelector(response.body)
    assert selector.has_node('form input[type="text"][name="name"]')
    assert selector.get_text('form button[type="submit"]') == "Execute"
    assert selector.get_text('form button[type="button"].btn-text') == "Cancel"


async def test_submit_valid_form(request_f: RequestFactory) -> None:
    request = request_f(
        method="POST", form_data={"name": "user"}, query_string="_ids=1"
    )
    action = MyAction()
    response = await action.dispatch(request)
    assert response.body == b"CALLED"


async def test_dangerous_variant(request_f: RequestFactory) -> None:
    request = request_f(method="GET", query_string="_ids=1")
    action = MyAction()
    action.dangerous = True
    response = await action.dispatch(request)
    selector = MarkupSelector(response.body)
    assert selector.has_class('form button[type="submit"]', "btn-danger")


async def test_confirmation(request_f: RequestFactory) -> None:
    request = request_f(method="GET", query_string="_ids=1")
    action = MyAction()
    response = await action.dispatch(request)
    selector = MarkupSelector(response.body)
    assert selector.get_text('form [data-test="confirmation"]') == (
        "Do you really want to appy this action on selected rows?"
    )
