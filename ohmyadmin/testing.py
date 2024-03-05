import bs4
import typing
from bs4 import BeautifulSoup


class SelectorError(Exception):
    ...


class NodeNotFoundError(SelectorError):
    ...


class MarkupSelector:
    def __init__(self, markup: str | bytes) -> None:
        if isinstance(markup, bytes):
            markup = markup.decode()
        self.root = BeautifulSoup(markup, multi_valued_attributes=False, features="html.parser")

    def find_node(self, selector: str) -> bs4.Tag | None:
        return self.root.select_one(selector)

    def find_node_or_raise(self, selector: str) -> bs4.Tag:
        if node := self.root.select_one(selector):
            return node
        raise NodeNotFoundError(f'No nodes: "{selector}".')

    def get_attribute(self, selector: str, attribute: str, default: typing.Any = None) -> str:
        return self.find_node_or_raise(selector).get(attribute, default)

    def has_attribute(self, selector: str, attribute: str) -> bool:
        return attribute in self.find_node_or_raise(selector).attrs

    def get_classes(self, selector: str) -> list[str]:
        return self.find_node_or_raise(selector).attrs.get("class", "").split(" ")

    def has_class(self, selector: str, *class_name: str) -> bool:
        classes = set(self.get_classes(selector))
        return len(classes.intersection(set(class_name))) == len(class_name)

    def get_styles(self, selector: str) -> dict[str, str]:
        return {
            css[0]: css[1]
            for css in [
                list(map(str.strip, style.split(":")))
                for style in self.get_attribute(selector, "style", "").split(";")
                if style
            ]
        }

    def get_style(self, selector: str, name: str) -> str:
        return self.get_styles(selector).get(name, "")

    def has_style(self, selector: str, name: str) -> bool:
        return name in self.get_styles(selector)

    def get_text(self, selector: str) -> str:
        node = self.find_node(selector)
        if node is None:
            return ""
        return node.text.strip()

    def has_text(self, selector: str, text: str) -> bool:
        return text in self.get_text(selector)

    def has_node(self, selector: str) -> bool:
        return self.find_node(selector) is not None

    def count(self, selector: str) -> int:
        return len(self.root.select(selector))
