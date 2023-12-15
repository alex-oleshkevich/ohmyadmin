import typing

COLOR_RED = "var(--o-color-red)"
COLOR_BLUE = "var(--o-color-blue)"
COLOR_YELLOW = "var(--o-color-yellow)"
COLOR_ORANGE = "var(--o-color-orange)"
COLOR_AMBER = "var(--o-color-amber)"
COLOR_GREEN = "var(--o-color-green)"
COLOR_PINK = "var(--o-color-pink)"
COLOR_TEAL = "var(--o-color-teal)"
COLOR_LIME = "var(--o-color-lime)"
COLOR_EMERALD = "var(--o-color-emerald)"
COLOR_SKY = "var(--o-color-sky)"
COLOR_INDIGO = "var(--o-color-indigo)"
COLOR_PURPLE = "var(--o-color-purple)"
COLOR_ROSE = "var(--o-color-rose)"


class ColorGenerator(typing.Protocol):
    def next(self) -> str:
        ...


class TailwindColors:
    def __init__(self) -> None:
        self._gen = color_generator()

    def next(self) -> str:
        return next(self._gen)


def color_generator() -> typing.Generator[str, None, None]:
    yield from [
        COLOR_RED,
        COLOR_YELLOW,
        COLOR_GREEN,
        COLOR_BLUE,
        COLOR_ROSE,
        COLOR_ORANGE,
        COLOR_LIME,
        COLOR_SKY,
        COLOR_PINK,
        COLOR_AMBER,
        COLOR_EMERALD,
        COLOR_INDIGO,
        COLOR_PURPLE,
        COLOR_TEAL,
    ]
