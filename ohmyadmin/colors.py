import typing

COLOR_RED = "var(--o-color-red)"
COLOR_RED_LIGHT = "var(--o-color-red-light)"
COLOR_BLUE = "var(--o-color-blue)"
COLOR_BLUE_LIGHT = "var(--o-color-blue-light)"
COLOR_YELLOW = "var(--o-color-yellow)"
COLOR_YELLOW_LIGHT = "var(--o-color-yellow-light)"
COLOR_ORANGE = "var(--o-color-orange)"
COLOR_ORANGE_LIGHT = "var(--o-color-orange-light)"
COLOR_AMBER = "var(--o-color-amber)"
COLOR_AMBER_LIGHT = "var(--o-color-amber-light)"
COLOR_GREEN = "var(--o-color-green)"
COLOR_GREEN_LIGHT = "var(--o-color-green-light)"
COLOR_PINK = "var(--o-color-pink)"
COLOR_PINK_LIGHT = "var(--o-color-pink-light)"
COLOR_TEAL = "var(--o-color-teal)"
COLOR_TEAL_LIGHT = "var(--o-color-teal-light)"
COLOR_LIME = "var(--o-color-lime)"
COLOR_LIME_LIGHT = "var(--o-color-lime-light)"
COLOR_EMERALD = "var(--o-color-emerald)"
COLOR_EMERALD_LIGHT = "var(--o-color-emerald-light)"
COLOR_SKY = "var(--o-color-sky)"
COLOR_SKY_LIGHT = "var(--o-color-sky-light)"
COLOR_INDIGO = "var(--o-color-indigo)"
COLOR_INDIGO_LIGHT = "var(--o-color-indigo-light)"
COLOR_PURPLE = "var(--o-color-purple)"
COLOR_PURPLE_LIGHT = "var(--o-color-purple-light)"
COLOR_ROSE = "var(--o-color-rose)"
COLOR_ROSE_LIGHT = "var(--o-color-rose-light)"


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
