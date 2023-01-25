from starlette.requests import Request
from unittest import mock

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.shortcuts import get_admin, render_to_response, render_to_string


def test_get_admin() -> None:
    """Tt should retrieve admin instance from the request."""
    admin = OhMyAdmin()
    request = Request({'type': 'http', 'state': {'admin': admin}})
    assert get_admin(request) == admin


def test_render_to_string() -> None:
    """Render_to_string should proxy to OhMyAdmin.render_to_string."""
    template = 'template.html'
    context = {'a': 'b'}
    with mock.patch('ohmyadmin.app.OhMyAdmin.render_to_string') as fn:
        admin = OhMyAdmin()
        request = Request({'type': 'http', 'state': {'admin': admin}})
        render_to_string(request, template, context)
    fn.assert_called_once_with(request, template, context)


def test_render_to_response() -> None:
    """Render_to_response should proxy to OhMyAdmin.render_to_string."""
    template = 'template.html'
    context = {'a': 'b'}
    with mock.patch('ohmyadmin.app.OhMyAdmin.render_to_response') as fn:
        admin = OhMyAdmin()
        request = Request({'type': 'http', 'state': {'admin': admin}})
        render_to_response(request, template, context)
    fn.assert_called_once_with(request, template, context)
