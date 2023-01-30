import wtforms
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin import actions, filters
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.metrics import ValueMetric
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn
from tests.models import Post

datasource = InMemoryDataSource(Post, [Post(id=x, title=f'Title {x}') for x in range(1, 100)])


class ExampleForm(wtforms.Form):
    title = wtforms.StringField(validators=[wtforms.validators.data_required()])


class ExamplePageAction(actions.BasePageAction):
    slug = 'example'
    label = 'Toast'

    async def apply(self, request: Request) -> Response:
        return Response('ok')


class ExampleObjectAction(actions.BaseObjectAction):
    slug = 'example'
    label = 'Toast'

    async def apply(self, request: Request, object_id: str) -> Response:
        return Response('ok')


class ExampleBatchAction(actions.BaseBatchAction):
    slug = 'example'
    label = 'Toast'

    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        return Response('ok')


class ExampleMetric(ValueMetric):
    label = 'Example'
    slug = 'example'

    async def calculate(self, request: Request) -> str:
        return 'CALLED'


class DemoResource(Resource):
    slug = 'demo'
    datasource = datasource
    form_class = ExampleForm
    columns = [
        TableColumn('title', searchable=True, sortable=True, link=True),
    ]
    page_actions = [
        actions.Link(url='/', label='Link Action'),
        ExamplePageAction(),
    ]
    object_actions = [
        ExampleObjectAction(),
    ]
    batch_actions = [
        ExampleBatchAction(),
    ]
    filters = [
        filters.StringFilter('title'),
    ]
    metrics = [
        ExampleMetric,
    ]
