import sqlalchemy as sa
import typing
from slugify import slugify

from ohmyadmin.helpers import camel_to_sentence


class ProjectionMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        if name != 'Projection':
            attrs['id'] = attrs.get('id', slugify(name.removesuffix('Projection')))
            attrs['label'] = attrs.get('label', camel_to_sentence(name.removesuffix('Projection')))

        return super().__new__(cls, name, bases, attrs)


class Projection(metaclass=ProjectionMeta):
    id: str = ''
    label: str = ''

    def __init__(self, label: str = '', id: str | None = None) -> None:
        self.id = id or self.id
        self.label = label or self.label

    def apply_filter(self, stmt: sa.sql.Select) -> sa.sql.Select:
        return stmt
