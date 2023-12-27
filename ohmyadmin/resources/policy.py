import abc
import typing

from starlette.requests import Request


class AccessPolicy(abc.ABC):
    @abc.abstractmethod
    def can_list(self, request: Request) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def can_create(self, request: Request) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def can_edit(self, request: Request, instance: typing.Any) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def can_delete(self, request: Request, instance: typing.Any) -> bool:
        raise NotImplementedError()


class PermissiveAccessPolicy:
    def can_list(self, request: Request) -> bool:
        return True

    def can_create(self, request: Request) -> bool:
        return True

    def can_edit(self, request: Request, instance: typing.Any) -> bool:
        return True

    def can_delete(self, request: Request, instance: typing.Any) -> bool:
        return True
