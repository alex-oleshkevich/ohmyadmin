from __future__ import annotations

import functools
import jinja2
import typing
from jinja2.runtime import Macro
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette_flash import flash
from tabler_icons import tabler_icon


def dict_to_attrs(attrs: dict[str, typing.Any]) -> str:
    result: list[str] = []
    for key, value in attrs.items():
        if value is None:
            continue
        if value is True or value is False:
            result.append(key)
            continue
        result.append(f'{key}="{value}"')

    return ' '.join(result)


class DynamicChoiceLoader(jinja2.ChoiceLoader):
    def add_loader(self, loader: jinja2.BaseLoader) -> None:
        typing.cast(list[jinja2.BaseLoader], self.loaders).insert(0, loader)


jinja_env = jinja2.Environment(
    extensions=['jinja2.ext.i18n', 'jinja2.ext.do'],
    loader=DynamicChoiceLoader(
        [
            jinja2.loaders.PackageLoader('ohmyadmin'),
        ]
    ),
)
jinja_env.globals.update(
    {
        # 'admin': self,
        'icon': tabler_icon,
        'tabler_icon': tabler_icon,
    }
)
jinja_env.tests.update({})
jinja_env.filters.update(
    {
        'dict_to_attrs': dict_to_attrs,
        'zip': zip,
    }
)
jinja_env.install_null_translations()  # type: ignore

_templates = Jinja2Templates('__irrelevant__')
_templates.env = jinja_env
TemplateResponse = _templates.TemplateResponse


def admin_context(request: Request) -> dict[str, typing.Any]:
    return {
        'request': request,
        'url': request.url_for,
        'main_menu': list(request.state.admin.build_main_menu(request)),
        'user_menu': request.state.admin.build_user_menu(request),
        'static': functools.partial(request.state.admin.static_url, request),
        'flash_messages': flash(request),
    }


def macro(template_name: str, macro_name: str) -> Macro:
    template = jinja_env.get_template(template_name)
    return getattr(template.module, macro_name)


def render_to_string(template_name: str, context: dict[str, typing.Any] | None = None) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(context or {})
