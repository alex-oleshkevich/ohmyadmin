from __future__ import annotations

import typing
from starlette.requests import Request

FlashCategory = typing.Literal['success', 'error']


class FlashFactory:
    def __init__(self, request: Request, message: str = '', category: FlashCategory = 'success') -> None:
        self.request = request
        self.message = message
        self.category = category

    def error(self, message: str) -> FlashFactory:
        self.category = 'error'
        self.message = message
        return self

    def success(self, message: str) -> FlashFactory:
        self.category = 'success'
        self.message = message
        return self


flash = FlashFactory
