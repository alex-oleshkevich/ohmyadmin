import typing
from starlette.requests import Request
from starlette.responses import Response


def render_to_string(request: Request, template_name: str, context: dict[str, typing.Any] | None = None) -> str:
    return request.state.admin.render(template_name, context)


def render_to_response(request: Request, template_name: str, context: dict[str, typing.Any] | None = None) -> Response:
    return request.state.admin.render_to_response(request, template_name, context)


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
