from __future__ import annotations

import typing
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

FlashCategory = typing.Literal['success', 'error']


class FlashMessage(typing.TypedDict):
    category: FlashCategory
    message: str


class FlashBag:
    def __init__(self, messages: list[FlashMessage] | None = None) -> None:
        print('FlashBag', messages)
        self.messages = messages or []

    def error(self, message: str) -> FlashBag:
        self.messages.append({'category': 'error', 'message': message})
        return self

    def success(self, message: str) -> FlashBag:
        self.messages.append({'category': 'success', 'message': message})
        return self

    def consume(self) -> list[FlashMessage]:
        """Return all messages and empty the bag."""
        messages = self.messages.copy()
        self.messages.clear()
        return messages

    def __bool__(self) -> bool:
        return len(self) > 0

    def __iter__(self) -> typing.Iterator[FlashMessage]:
        return iter(self.consume())

    def __len__(self) -> int:
        return len(self.messages)


def flash(request: Request) -> FlashBag:
    return request.state.flash_messages


class FlashMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not scope['type'] == 'http':
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        session = request.session
        if load_method := getattr(session, 'load', None):
            await load_method()

        stored_messages = request.session.get('flash_messages', [])
        bag = FlashBag(stored_messages)
        request.state.flash_messages = bag

        async def _send(message: Message) -> None:
            if message['type'] == 'http.response.start':
                request.session['flash_messages'] = bag.messages
            await send(message)

        await self.app(scope, receive, _send)
