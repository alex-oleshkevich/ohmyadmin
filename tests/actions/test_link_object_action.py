from starlette.requests import Request

from ohmyadmin.actions import ObjectLink
from ohmyadmin.helpers import LazyURL
from ohmyadmin.testing import MarkupSelector
from tests.models import Post

model = Post(id=10, title='Object')


def test_action_renders_template(http_request: Request) -> None:
    page = ObjectLink(label='Item', url='/')
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.get_text('a') == 'Item'
    assert selector.get_attribute('a', 'href') == '/'
    assert selector.has_class('a', 'list-menu-item')
    assert not selector.has_node('a svg')


def test_action_renders_template_with_lazy_url(http_request: Request) -> None:
    page = ObjectLink(label='Item', url=LazyURL(path_name='posts', path_params={'id': '100'}))
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.get_attribute('a', 'href') == 'http://testserver/admin/posts/100'


def test_action_renders_template_with_lazy_object_url(http_request: Request) -> None:
    page = ObjectLink(label='Item', url=lambda r, o: r.url_for('posts', id=o.id))
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.get_attribute('a', 'href') == 'http://testserver/admin/posts/10'


def test_action_renders_template_with_icon(http_request: Request) -> None:
    page = ObjectLink(label='Item', url='/', icon='plus')
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.has_node('a svg')
