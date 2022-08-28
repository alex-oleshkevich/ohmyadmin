import dataclasses

from starlette.requests import Request


@dataclasses.dataclass
class MenuItem:
    label: str
    url: str
    icon: str = ''
    rel = 'nofollow'

    def render(self, request: Request) -> str:
        return self.url

    @classmethod
    def to_dashboard(cls, dashboard_id: str, label: str = '', icon: str = '') -> None:
        pass

    @classmethod
    def to_resource(cls, resource_id: str, label: str = '', icon: str = '') -> None:
        pass

    @classmethod
    def to_url(cls, text: str, url: str) -> None:
        pass

    @classmethod
    def submit_link(cls, label: str, action_url: str, icon: str = '', dangerous: bool = False) -> None:
        pass


class MenuGroup(MenuItem):
    def __init__(self, label: str, items: list[MenuItem]) -> None:
        self.label = label
        self.items = items
