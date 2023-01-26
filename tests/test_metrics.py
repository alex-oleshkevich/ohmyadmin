from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.metrics import (
    Card,
    PartitionMetric,
    PartitionResult,
    ProgressMetric,
    TrendMetric,
    TrendResult,
    ValueMetric,
)
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory


class ExampleCard(Card):
    async def dispatch(self, request: Request) -> Response:
        return Response('CARD CONTENT')


def test_autogenerates_slug() -> None:
    card = ExampleCard()
    assert card.slug == 'examplecard'


def test_autogenerates_label() -> None:
    card = ExampleCard()
    assert card.label == 'Example Card'


def test_generates_url(request_f: RequestFactory) -> None:
    card = ExampleCard()
    request = request_f()
    assert str(card.resolve_url(request)) == 'http://testserver/admin/?_metric=examplecard'


async def test_renders_title(request_f: RequestFactory) -> None:
    class ExampleMetric(ValueMetric):
        label = 'Example Metric'

        async def calculate(self, request: Request) -> str:
            return 'HUNDRED'

    card = ExampleMetric()
    request = request_f()
    response = await card.dispatch(request)
    page = MarkupSelector(response.body)
    assert page.get_node_text('[data-test="metric"] header') == 'Example Metric'


async def test_value_metric(request_f: RequestFactory) -> None:
    class ExampleMetric(ValueMetric):
        async def calculate(self, request: Request) -> str:
            return 'HUNDRED'

    card = ExampleMetric()
    request = request_f()
    response = await card.dispatch(request)
    page = MarkupSelector(response.body)
    assert page.get_node_text('[data-test="metric"] main') == 'HUNDRED'


async def test_trend_metric(request_f: RequestFactory) -> None:
    class ExampleMetric(TrendMetric):
        async def calculate(self, request: Request) -> TrendResult:
            return TrendResult(current_value=100, series=[('zero', 10), ('one', 20)])

    card = ExampleMetric()
    request = request_f()
    response = await card.dispatch(request)
    page = MarkupSelector(response.body)

    # current value rendered
    assert page.get_node_text('[data-test="metric"] main [data-test="trend-current"]') == '100'

    # renders script data
    assert page.get_node_text('[data-test="metric"] main script') == '[["zero", 10], ["one", 20]]'

    # renders chart tag
    assert page.has_node('[data-test="metric"] main x-trend-metric-chart')


async def test_progress_metric(request_f: RequestFactory) -> None:
    class ExampleMetric(ProgressMetric):
        target = 100

        async def calculate(self, request: Request) -> float | int:
            return 20

    card = ExampleMetric()
    request = request_f()
    response = await card.dispatch(request)
    page = MarkupSelector(response.body)

    # current value rendered
    assert page.get_node_text('[data-test="metric"] main [data-test="progress-current"]') == '20%'

    # renders chart tag
    assert (
        page.find_node('[data-test="metric"] main [data-test="progress-value"] .progress-bar')['style'] == 'width: 20%'
    )


async def test_partition_metric(request_f: RequestFactory) -> None:
    class ExampleMetric(PartitionMetric):
        async def calculate(self, request: Request) -> PartitionResult:
            return PartitionResult(
                groups={
                    'red': {'color': 'red', 'value': 30},
                    'blue': {'color': 'blue', 'value': 70},
                }
            )

    card = ExampleMetric()
    request = request_f()
    response = await card.dispatch(request)
    page = MarkupSelector(response.body)

    # renders table
    table_text = page.get_node_text('[data-test="metric"] main [data-test="partition-table"]')
    assert 'red' in table_text
    assert 'blue' in table_text

    # renders script data
    assert (
        page.get_node_text('[data-test="metric"] main script')
        == '{"blue": {"color": "blue", "value": 70}, "red": {"color": "red", "value": 30}}'
    )

    # renders chart tag
    assert page.has_node('[data-test="metric"] main x-partition-metric-chart')
