import jinja2
import typing
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
