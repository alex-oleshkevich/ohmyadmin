import typing
from starlette.requests import Request
from starlette.responses import Response
from unittest import mock

from ohmyadmin import actions
from ohmyadmin.filters import BaseFilter, UnboundFilter


class HasPageActions:
    page_actions: typing.Sequence[actions.PageAction] | None = None

    def get_page_actions(self, _: Request) -> list[actions.PageAction]:
        return list(self.page_actions or [])

    async def dispatch_action(self, request: Request, action_slug: str) -> Response:
        actions_ = {
            action.slug: action for action in self.get_page_actions(request) if isinstance(action, actions.Dispatch)
        }

        try:
            action = actions_[action_slug]
        except KeyError:
            raise ValueError(f'Action "{action_slug}" is not defined.')

        return await action.dispatch(request)

    async def handler(self, request: Request) -> Response:
        if '_action' in request.query_params:
            return await self.dispatch_action(request, request.query_params['_action'])

        return await super().handler(request)


class HasObjectActions:
    object_actions: typing.Sequence[actions.ObjectAction] | None = None

    def get_object_actions(self, request: Request, obj: typing.Any) -> list[actions.ObjectAction]:
        return list(self.object_actions or [])

    async def dispatch_object_action(self, request: Request, action_slug: str) -> Response:
        actions_ = {
            action.slug: action
            for action in self.get_object_actions(request, mock.MagicMock()) or []
            if isinstance(action, actions.Dispatch)
        }

        try:
            action = actions_[action_slug]
        except KeyError:
            raise ValueError(f'Object action "{action_slug}" is not defined.')

        return await action.dispatch(request)

    async def handler(self, request: Request) -> Response:
        if '_object_action' in request.query_params:
            return await self.dispatch_object_action(request, request.query_params['_object_action'])

        return await super().handler(request)


class HasBatchActions:
    batch_actions: typing.Sequence[actions.BatchAction] | None = None

    def get_batch_actions(self, request: Request) -> list[actions.BatchAction]:
        return list(self.batch_actions or [])

    async def dispatch_batch_action(self, request: Request, action_slug: str) -> Response:
        actions_ = {action.slug: action for action in self.get_batch_actions(request)}
        try:
            action = actions_[action_slug]
        except KeyError:
            raise ValueError(f'Batch action "{action_slug}" is not defined.')

        return await action.dispatch(request)

    async def handler(self, request: Request) -> Response:
        if '_batch_action' in request.query_params:
            return await self.dispatch_batch_action(request, request.query_params['_batch_action'])

        return await super().handler(request)


class HasFilters:
    filters: typing.Sequence[UnboundFilter] | None = None

    def get_filters(self, request: Request) -> typing.Sequence[UnboundFilter]:
        return self.filters or []

    async def create_filters(self, request: Request) -> list[BaseFilter]:
        return [await _filter.create(request) for _filter in self.get_filters(request)]
