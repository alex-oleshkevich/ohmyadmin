from unittest import mock

from ohmyadmin.actions import DeleteObjectAction
from ohmyadmin.datasources.datasource import DataSource
from tests.conftest import RequestFactory


async def test_confirmation(request_f: RequestFactory) -> None:
    request = request_f(method="GET", query_string="_ids=1")
    action = DeleteObjectAction()
    assert action.dangerous
    response = await action.dispatch(request)
    assert "Unsupported HTTP method." in response.headers["hx-trigger"]


async def test_dispatch(request_f: RequestFactory, datasource: DataSource) -> None:
    request = request_f(
        method="POST", query_string="_ids=1", state={"datasource": datasource}
    )
    action = DeleteObjectAction()
    with mock.patch.object(datasource, "delete") as fn:
        response = await action.dispatch(request)
        assert "Title 1 has been deleted." in response.headers["hx-trigger"]
    fn.assert_awaited_once()
