import pathlib
from starlette.responses import Response
from starlette.routing import Route

from ohmyadmin.helpers import LazyURL
from ohmyadmin.menu import MenuGroup, MenuLink
from tests.conftest import RequestFactory


def test_menu_link_is_active(request_f: RequestFactory) -> None:
    item = MenuLink(text='Item', url='/admin/users')
    assert item.is_active(request_f(path='/users'))
    assert not item.is_active(request_f(path='/blog'))


def test_menu_link_is_active_with_lazy(request_f: RequestFactory) -> None:
    request = request_f(routes=[Route('/users', name='users', endpoint=Response('ok'))], path='/users')
    item = MenuLink(text='Item', url=LazyURL('users'))
    assert item.is_active(request)


def test_menu_link_is_active_with_lazy_with_params(request_f: RequestFactory) -> None:
    request = request_f(routes=[Route('/users/{id}', name='users', endpoint=Response('ok'))], path='/users/100')
    item = MenuLink(text='Item', url=LazyURL('users', path_params={'id': '100'}))
    assert item.is_active(request)

    request = request_f(routes=[Route('/users/{id}', name='users', endpoint=Response('ok'))], path='/users/101')
    item = MenuLink(text='Item', url=LazyURL('users', path_params={'id': '100'}))
    assert not item.is_active(request)


def test_menu_link_resolve_string(request_f: RequestFactory) -> None:
    item = MenuLink(text='Item', url='/admin/users')
    assert item.resolve(request_f()) == '/admin/users'


def test_menu_link_resolve_lazy(request_f: RequestFactory) -> None:
    request = request_f(routes=[Route('/users', name='users', endpoint=Response('ok'))])
    item = MenuLink(text='Item', url=LazyURL('users'))
    assert item.resolve(request) == 'http://testserver/admin/users'


def test_menu_link_resolve_lazy_with_params(request_f: RequestFactory) -> None:
    request = request_f(routes=[Route('/users/{id}', name='users', endpoint=Response('ok'))])
    item = MenuLink(text='Item', url=LazyURL('users', path_params={'id': '100'}))
    assert item.resolve(request) == 'http://testserver/admin/users/100'


def test_menu_link_render(request_f: RequestFactory) -> None:
    request = request_f()
    item = MenuLink(text='Item', url='/')
    content = item.render(request)
    assert 'Item' in content
    assert 'href="/"' in content


def test_menu_link_template_context(request_f: RequestFactory, extra_template_dir: pathlib.Path) -> None:
    (extra_template_dir / 'ohmyadmin').mkdir(parents=True)
    (extra_template_dir / 'ohmyadmin/menu_item_link.html').write_text(
        "'has_item' if item is not null else ''\n" "'is_active' if item is not null else ''\n"
    )
    request = request_f()
    item = MenuLink(text='Item', url='/')
    content = item.render(request)
    assert 'has_item' in content
    assert 'is_active' in content


def test_menu_group_iterable(request_f: RequestFactory) -> None:
    item = MenuLink('Item 1', url='/')
    group = MenuGroup(text='Group', items=[item])
    assert next(iter(group)) == item


def test_menu_group_is_active(request_f: RequestFactory) -> None:
    item = MenuLink('Item 1', url='/admin/users')
    group = MenuGroup(text='Group', items=[item])
    assert group.is_active(request_f(path='/users'))
    assert not group.is_active(request_f(path='/posts'))


def test_menu_group_render(request_f: RequestFactory) -> None:
    request = request_f()
    item = MenuLink('Item 1', url='/admin/users')
    group = MenuGroup(text='Group', items=[item])
    content = group.render(request)
    assert 'Group' in content
    assert 'Item 1' in content
    assert 'href="/admin/users"' in content
