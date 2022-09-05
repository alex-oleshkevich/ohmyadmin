import abc
from starlette.requests import Request


class View(abc.ABC):
    def __call__(self, request: Request) -> str:
        return self.render(request)

    @abc.abstractmethod
    def render(self, request: Request) -> str:
        ...
