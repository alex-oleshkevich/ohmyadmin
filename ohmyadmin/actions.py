from __future__ import annotations

import dataclasses

import enum
import typing

from ohmyadmin.flash import FlashCategory

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import Resource, ResourceAction


class ActionResponse:
    class Type(str, enum.Enum):
        TOAST = 'toast'
        REDIRECT = 'redirect'
        REFRESH = 'refresh'

    @dataclasses.dataclass
    class ToastOptions:
        message: str
        category: FlashCategory

    @dataclasses.dataclass
    class RedirectOptions:
        url: str | None = None
        path_name: str | None = None
        path_params: typing.Mapping[str, str | int] | None = None
        resource: typing.Type[Resource] | Resource | None = None
        resource_action: ResourceAction = 'list'

    def __init__(
        self, type: str, toast_options: ToastOptions | None = None, redirect_options: RedirectOptions | None = None
    ) -> None:
        self.type = type
        self.toast_options = toast_options
        self.redirect_options = redirect_options

    def with_success(self, message: str) -> ActionResponse:
        self.toast_options = self.ToastOptions(message=message, category='success')
        return self

    def with_error(self, message: str) -> ActionResponse:
        self.toast_options = self.ToastOptions(message=message, category='error')
        return self

    @classmethod
    def toast(cls, message: str, category: FlashCategory = 'success') -> ActionResponse:
        return ActionResponse(type=cls.Type.TOAST, toast_options=cls.ToastOptions(message=message, category=category))

    @classmethod
    def redirect(cls, url: str) -> ActionResponse:
        return ActionResponse(type=cls.Type.REDIRECT, redirect_options=cls.RedirectOptions(url=url))

    @classmethod
    def redirect_to_path_name(
        cls, path_name: str | None = None, path_params: typing.Mapping[str, str | int] | None = None
    ) -> ActionResponse:
        return ActionResponse(
            type=cls.Type.REDIRECT,
            redirect_options=cls.RedirectOptions(path_name=path_name, path_params=path_params or {}),
        )

    @classmethod
    def redirect_to_resource(
        cls,
        resource: typing.Type[Resource] | Resource,
        action: ResourceAction = 'list',
    ) -> ActionResponse:
        return ActionResponse(
            type=cls.Type.REDIRECT,
            redirect_options=cls.RedirectOptions(
                resource=resource,
                resource_action=action,
            ),
        )

    @classmethod
    def refresh(cls) -> ActionResponse:
        return ActionResponse(type=cls.Type.REFRESH)
