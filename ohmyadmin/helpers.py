from __future__ import annotations

import re
import typing
from starlette.requests import Request

from ohmyadmin.globals import get_current_admin, get_current_request
from ohmyadmin.responses import Response
from ohmyadmin.templating import jinja_env

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import PkType, Resource, ResourceAction


def render_to_string(template_name: str, context: dict[str, typing.Any] | None = None) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(context or {})


def render_to_response(
    request: Request, template_name: str, context: dict[str, typing.Any] | None = None, status_code: int = 200
) -> Response:
    return get_current_admin().render_to_response(request, template_name, context, status_code)


def camel_to_sentence(text: str) -> str:
    """
    Convert camel cased strings (like class names) into a sentence.

    Example: OrderItemsResource -> Order items resource.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text)


def url(path_name: str, **path_params: str | int) -> str:
    return get_current_request().url_for(path_name, **(path_params or {}))


def media_url(path: str) -> str:
    return get_current_request().url_for('ohmyadmin_media', path=path)


def resource_url(
    resource: typing.Type[Resource] | Resource,
    action: ResourceAction = 'list',
    pk: PkType | None = None,
) -> str:
    kwargs = {'pk': pk} if pk else {}
    return get_current_request().url_for(resource.get_route_name(action), **kwargs)


def pluralize(text: str) -> str:
    """
    A simple pluralization utility.

    It adds -ies suffix to any noun that ends with -y, it adds -es suffix to any
    noun that ends with -s. For all other cases it appends -s.
    """
    if text.endswith('y'):
        return text[:-1] + 'ies'
    if text.endswith('s'):
        return text + 'es'
    return text + 's'
