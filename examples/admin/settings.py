from starlette.requests import Request
from starlette.responses import Response
from starlette_flash import flash

from ohmyadmin.pages.page import TemplatePage


class SettingsPage(TemplatePage):
    icon = 'settings'
    label_plural = 'Settings'
    group = 'Settings'
    template = 'settings_page.html'

    def post(self, request: Request) -> Response:
        flash(request).success('Operation successful.')
        return self.redirect_to_self(request)
