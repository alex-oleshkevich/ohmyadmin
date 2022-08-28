from starlette.requests import Request


class View:
    def render(self, request: Request) -> str:
        ...
