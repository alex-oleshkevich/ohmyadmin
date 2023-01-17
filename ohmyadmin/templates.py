import typing
from markupsafe import Markup


def as_html_attrs(value: typing.Mapping) -> str:
    def resolve_attr_name(name: str) -> str:
        if name.startswith('data') or name.startswith('aria'):
            return name.replace('_', '-')
        return name

    parts: list[str] = []
    for attr_name, attr_value in value.items():
        attr_name = resolve_attr_name(attr_name)
        if not value:
            continue
        if value is True:
            parts.append(attr_name)
            continue
        parts.append(f'{attr_name}="{attr_value}"')
    return Markup(' '.join(parts))
