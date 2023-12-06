from unittest import mock

from ohmyadmin.actions import BatchDelete
from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory


async def test_confirmation(request_f: RequestFactory) -> None:
    request = request_f(method="GET", query_string="_ids=1")
    action = BatchDelete()
    assert action.dangerous
    response = await action.dispatch(request)
    selector = MarkupSelector(response.body)
    assert selector.get_text('form [data-test="confirmation"]') == (
        "Are you sure you want to delete selected objects?"
    )


async def test_dispatch(request_f: RequestFactory, datasource: DataSource) -> None:
    request = request_f(
        method="POST", query_string="_ids=1", state={"datasource": datasource}
    )
    action = BatchDelete()
    with mock.patch.object(datasource, "delete") as fn:
        response = await action.dispatch(request)
        assert "1 records has been deleted." in response.headers["hx-trigger"]
    fn.assert_awaited_once()
