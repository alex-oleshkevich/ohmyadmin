import enum
import typing
from starlette.requests import Request


class ChoicePopulator(typing.Protocol):
    async def __call__(self, request: Request) -> list[tuple[str, str]]:
        ...


class ChoicedEnumMeta(enum.EnumMeta):  # noqa
    _value2label_map_: dict
    label: typing.Any

    def __new__(metacls, classname: str, bases: tuple, classdict: typing.Any, **kwds: typing.Any) -> typing.Type:
        labels = []
        for key in classdict._member_names:
            value = classdict[key]
            if isinstance(value, (list, tuple)) and len(value) > 1:
                *value, label = value
                value = tuple(value)
            else:
                label = key.replace('_', ' ').title()
            labels.append(label)
            # Use dict.__setitem__() to suppress defenses against double
            # assignment in enum's classdict.
            dict.__setitem__(classdict, key, value)
        cls = super().__new__(metacls, classname, bases, classdict, **kwds)
        cls._value2label_map_ = dict(zip(cls._value2member_map_, labels))
        # Add a label property to instances of enum which uses the enum member
        # that is passed in as "self" as the value to use when looking up the
        # label in the choices.
        cls.label = property(lambda self: cls._value2label_map_.get(self.value))
        return enum.unique(cls)  # type:ignore

    def __contains__(cls, member: typing.Any) -> bool:
        if not isinstance(member, enum.Enum):
            # Allow non-enums to match against member values.
            return any(x.value == member for x in cls)  # type: ignore
        return super().__contains__(member)  # type: ignore

    @property
    def names(cls) -> list[str]:
        empty = ['__empty__'] if hasattr(cls, '__empty__') else []
        return empty + [member.name for member in cls]  # type: ignore

    @property
    def choices(cls) -> list[tuple[typing.Any, str]]:
        empty = [(None, cls.__empty__)] if hasattr(cls, '__empty__') else []  # type: ignore
        return empty + [(member.value, member.label) for member in cls]  # type: ignore

    @property
    def labels(cls) -> list[str]:
        return [label for _, label in cls.choices]

    @property
    def values(cls) -> list[typing.Any]:
        return [value for value, _ in cls.choices]


class Choices(enum.Enum, metaclass=ChoicedEnumMeta):
    def __str__(self) -> str:
        """Use value when cast to str, so that Choices set as model instance
        attributes are rendered as expected in templates and similar
        contexts."""
        return str(self.value)


class TextChoices(str, Choices):
    """Class for creating enumerated string choices."""

    def _generate_next_value_(name, start: int, count: int, last_values: list[typing.Any]) -> typing.Any:  # type:ignore
        return name


class IntegerChoices(int, Choices):
    """Class for creating enumerated integer choices."""
