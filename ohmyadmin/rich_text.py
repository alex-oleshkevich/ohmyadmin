from __future__ import annotations

import typing

from ohmyadmin.templating import macro


class EditorAction:
    icon: str = ''
    action: str = ''
    label: str = ''
    title: str = ''
    widget: typing.ClassVar[typing.Callable[['EditorAction'], str]] = macro(
        'ohmyadmin/forms/rich_text.html', 'simple_toolbar_button'
    )

    def __str__(self) -> str:
        return self.widget(self)  # type: ignore


class Bold(EditorAction):
    icon: str = 'bold'
    action: str = 'bold'


class Italic(EditorAction):
    icon: str = 'italic'
    action: str = 'italic'


class Quote(EditorAction):
    icon: str = 'blockquote'
    action: str = 'blockquote'


class BulletList(EditorAction):
    icon = 'list'
    action = 'bullet_list'


class OrderedList(EditorAction):
    icon = 'list-numbers'
    action = 'bullet_list'


class Code(EditorAction):
    icon = 'code'
    action = 'code'


class CodeBlock(EditorAction):
    icon = 'source-code'
    action = 'code_block'


class Link(EditorAction):
    icon = 'link'
    action = 'link'


class Highlight(EditorAction):
    icon = 'highlight'
    action = 'highlight'
    args = {'color': '#ffcc00'}


class Heading(EditorAction):
    icon = 'heading'
    action = 'highlight'
    widget = macro('ohmyadmin/forms/rich_text.html', 'heading_button')

    def __init__(self, levels: list[int] | None = None) -> None:
        self.levels = levels or [1, 2, 3, 4, 5, 6]


class Separator(EditorAction):
    widget = macro('ohmyadmin/forms/rich_text.html', 'toolbar_separator')


class EditorToolbar:
    def __init__(self, actions: list[EditorAction]) -> None:
        self.actions = actions

    def __iter__(self) -> typing.Iterator[EditorAction]:
        return iter(self.actions)
