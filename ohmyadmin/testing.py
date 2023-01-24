import bs4
from bs4 import BeautifulSoup


class MarkupSelector:
    def __init__(self, markup: str) -> None:
        self.root = BeautifulSoup(markup)

    def find_node(self, selector: str) -> bs4.Tag:
        return self.root.select_one(selector)

    def find_nodes(self, selector: str) -> bs4.ResultSet[bs4.Tag]:
        return self.root.select(selector)

    def get_node_text(self, selector: str) -> str:
        return self.find_node(selector).text.strip()

    def has_node(self, selector: str) -> bool:
        return self.find_node(selector) is not None

    def count(self, selector: str) -> int:
        return len(self.root.select(selector))
