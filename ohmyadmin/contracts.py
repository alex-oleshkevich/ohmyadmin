import typing

from ohmyadmin.actions import actions


@typing.runtime_checkable
class HasOrderingParam(typing.Protocol):
    def get_ordering_param(self) -> str:
        ...


@typing.runtime_checkable
class HasBatchActions(typing.Protocol):
    def get_batch_actions(self) -> typing.Sequence[actions.ModalAction]:
        ...


@typing.runtime_checkable
class HasObjectActions(typing.Protocol):
    def get_object_actions(self) -> typing.Sequence[actions.Action]:
        ...


@typing.runtime_checkable
class HasOrderingFields(typing.Protocol):
    def get_ordering_fields(self) -> typing.Sequence[actions.Action]:
        ...
