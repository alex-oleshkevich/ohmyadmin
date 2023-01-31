import typing
import wtforms
from starlette.datastructures import URL, FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.types import Receive, Scope, Send
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin import actions, layouts
from ohmyadmin.actions import ActionResponse, BatchDelete, DeleteObjectAction
from ohmyadmin.datasource.base import DataSource
from ohmyadmin.filters import BaseFilter, UnboundFilter
from ohmyadmin.forms import populate_object
from ohmyadmin.helpers import LazyObjectURL, LazyURL
from ohmyadmin.metrics import Card
from ohmyadmin.pages.base import BasePage
from ohmyadmin.pages.form import FormPage
from ohmyadmin.pages.table import TablePage
from ohmyadmin.views.table import TableColumn


class Resource(BasePage, Router):
    group = _('Resources', domain='ohmyadmin')
    form_class: type[wtforms.Form] = wtforms.Form
    datasource: DataSource
    page_param: typing.ClassVar[str] = 'page'
    page_size_param: typing.ClassVar[str] = 'page_size'
    search_param: typing.ClassVar[str] = 'search'
    ordering_param: typing.ClassVar[str] = 'ordering'
    page_size: typing.ClassVar[int] = 25
    max_page_size: typing.ClassVar[int] = 100
    columns: typing.Sequence[TableColumn] | None = None
    page_actions: typing.Sequence[actions.PageAction] | None = None
    object_actions: typing.Sequence[actions.ObjectAction] | None = None
    batch_actions: typing.Sequence[actions.BatchAction] | None = None
    filters: typing.Sequence[UnboundFilter | BaseFilter] | None = None
    metrics: typing.Sequence[type[Card]] | None = None
    create_form_actions: typing.Sequence[actions.Submit | actions.Link] | None = None
    update_form_actions: typing.Sequence[actions.Submit | actions.Link] | None = None

    def __init__(self) -> None:
        super().__init__(routes=self.get_routes())

    def get_table_columns(self, request: Request) -> typing.Sequence[TableColumn]:
        columns = list(self.columns or [])
        for column in columns:
            if column.link is True:
                column.link = LazyObjectURL(
                    lambda r, o: URL(request.url_for(self.get_path_name() + '.edit', pk=self.datasource.get_pk(o)))
                )

        return columns

    def get_page_actions(self, request: Request) -> list[actions.PageAction]:
        create_route_name = self.get_path_name() + '.create'
        return [
            *(self.page_actions or []),
            actions.Link(
                label=_('Create', domain='ohmyadmin'),
                url=LazyURL(create_route_name),
                variant='accent',
                icon='plus',
            ),
        ]

    def get_object_actions(self, request: Request, obj: typing.Any) -> list[actions.ObjectAction]:
        edit_route_name = self.get_path_name() + '.edit'
        return [
            *(self.object_actions or []),
            actions.ObjectLink(
                label=_('Edit', domain='ohmyadmin'),
                icon='pencil',
                url=LazyURL(path_name=edit_route_name, path_params={'pk': self.datasource.get_pk(obj)}),
            ),
            DeleteObjectAction(),
        ]

    def get_batch_actions(self, request: Request) -> list[actions.BatchAction]:
        return [*(self.batch_actions or []), BatchDelete()]

    def get_filters(self, request: Request) -> typing.Sequence[UnboundFilter | BaseFilter]:
        return self.filters or []

    def get_metrics(self, request: Request) -> typing.Sequence[Card]:
        return [metric() for metric in self.metrics or []]

    def build_form_layout(self, request: Request, form: wtforms.Form) -> layouts.Layout:
        return layouts.Card([layouts.StackedForm([layouts.Input(field) for field in form])])

    def get_create_form_actions(self, request: Request) -> typing.Sequence[actions.Submit | actions.Link]:
        return self.create_form_actions or [
            actions.Submit(label=_('Create and return to list', domain='ohmyadmin'), variant='accent', name='_return'),
            actions.Submit(label=_('Create and edit', domain='ohmyadmin'), name='_edit'),
            actions.Submit(label=_('Create and add new', domain='ohmyadmin'), name='_add_new'),
        ]

    def get_create_view_response(self, request: Request, form_data: FormData, model: typing.Any) -> Response:
        flash(request).success(_('{object} has been created.', domain='ohmyadmin').format(object=model))
        if '_edit' in form_data:
            return ActionResponse().redirect(
                request,
                request.url_for(
                    name=self.get_path_name() + '.edit',
                    pk=self.datasource.get_pk(model),
                ),
            )
        if '_add_new' in form_data:
            return ActionResponse().redirect(request, request.url_for(name=self.get_path_name() + '.create'))
        return ActionResponse().redirect(request, self.generate_url(request))

    def get_update_form_actions(self, request: Request) -> typing.Sequence[actions.Submit | actions.Link]:
        return self.update_form_actions or [
            actions.Submit(label=_('Update and return to list', domain='ohmyadmin'), variant='accent', name='_return'),
            actions.Submit(label=_('Update and continue editing', domain='ohmyadmin'), name='_continue'),
            actions.Link(label=_('Return to list', domain='ohmyadmin'), url=self.generate_url(request)),
        ]

    def get_update_view_response(self, request: Request, form_data: FormData, model: typing.Any) -> Response:
        message = _('{object} has been updated.', domain='ohmyadmin').format(object=model)
        if '_continue' not in form_data:
            flash(request).success(_('{object} has been updated.', domain='ohmyadmin').format(object=model))
            return ActionResponse().redirect(request, self.generate_url(request))
        return ActionResponse().show_toast(message)

    async def index_view(self, request: Request) -> Response:
        page_class = type(
            'IndexPage',
            (TablePage,),
            dict(
                page_title=self.page_title,
                label=self.label,
                label_plural=self.label_plural,
                datasource=self.datasource,
                page_param=self.page_param,
                page_size=self.page_size,
                page_size_param=self.page_size_param,
                search_param=self.search_param,
                ordering_param=self.ordering_param,
                max_page_size=self.max_page_size,
                filters=self.get_filters(request),
                get_metrics=self.get_metrics,
                get_page_actions=self.get_page_actions,
                get_object_actions=self.get_object_actions,
                get_batch_actions=self.get_batch_actions,
                get_table_columns=self.get_table_columns,
            ),
        )

        page = page_class()
        return await page.dispatch(request)

    async def create_empty_model(self, request: Request) -> typing.Any:
        return self.datasource.new()

    async def get_object(self, request: Request) -> typing.Any:
        pk = request.path_params['pk']
        return await self.datasource.get(request, pk)

    async def perform_create(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        await populate_object(request, form, model)
        await self.datasource.create(request, model)
        form_data = await request.form()
        return self.get_create_view_response(request, form_data, model)

    async def perform_update(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:
        await populate_object(request, form, model)
        await self.datasource.update(request, model)
        form_data = await request.form()
        return self.get_update_view_response(request, form_data, model)

    async def create_view(self, request: Request) -> Response:
        page_class = type(
            'CreateFormPage',
            (FormPage,),
            dict(
                label='Create {label_singular}'.format(label_singular=self.label),
                form_class=self.form_class,
                form_actions=self.get_create_form_actions(request),
                build_form_layout=self.build_form_layout,
                get_form_object=self.create_empty_model,
                handle_submit=self.perform_create,
            ),
        )

        page = page_class()
        return await page.dispatch(request)

    async def update_view(self, request: Request) -> Response:
        page_class = type(
            'UpdateFormPage',
            (FormPage,),
            dict(
                label='Update {label_singular}'.format(label_singular=self.label),
                form_class=self.form_class,
                form_actions=self.get_update_form_actions(request),
                build_form_layout=self.build_form_layout,
                get_form_object=self.get_object,
                handle_submit=self.perform_update,
            ),
        )

        page = page_class()
        return await page.dispatch(request)

    async def delete_view(self, request: Request) -> Response:
        pk = request.path_params['pk']
        model = await self.datasource.get(request, pk)
        if request.method in ['POST', 'DELETE']:
            await self.datasource.delete(request, pk)
            flash(request).success(_('{object} has been deleted.', domain='ohmyadmin'))

            redirect_to = self.generate_url(request)
            if 'hx-request' in request.headers:
                return ActionResponse().redirect(request, redirect_to)
            return RedirectResponse(redirect_to, 302)

        cancel_url = self.generate_url(request)
        return self.render_to_response(
            request,
            'ohmyadmin/resources/delete.html',
            {
                'page_title': _('Delete {object}', domain='ohmyadmin').format(object=model),
                'object': model,
                'cancel_url': cancel_url,
            },
        )

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route(
                '/',
                self.index_view,
                name=f'{self.get_path_name()}.index',
                methods=['get', 'post', 'put', 'patch', 'delete'],
            ),
            Route('/new', self.create_view, name=f'{self.get_path_name()}.create', methods=['get', 'post']),
            Route('/{pk}/edit', self.update_view, name=f'{self.get_path_name()}.edit', methods=['get', 'post']),
            Route(
                '/{pk}/delete',
                self.delete_view,
                name=f'{self.get_path_name()}.delete',
                methods=['get', 'post', 'delete'],
            ),
        ]

    def as_route(self) -> Mount:
        return Mount(f'/resources/{self.slug}', self)

    @classmethod
    def generate_url(cls, request: Request) -> str:
        return request.url_for(f'{cls.get_path_name()}.index')

    @classmethod
    def get_path_name(cls) -> str:
        return f'ohmyadmin.resources.{cls.slug}'

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope['state']['page'] = self
        scope['state']['datasource'] = self.datasource
        return await super().__call__(scope, receive, send)
