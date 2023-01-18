import sqlalchemy as sa
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.config import async_session
from examples.models import Product
from ohmyadmin import actions
from ohmyadmin.actions import ActionResponse, BaseBatchAction
from ohmyadmin.datasource.sqla import SQLADataSource
from ohmyadmin.filters import (
    ChoiceFilter,
    DateFilter,
    DateRangeFilter,
    DecimalFilter,
    FloatFilter,
    IntegerFilter,
    MultiChoiceFilter,
    StringFilter,
)
from ohmyadmin.formatters import BoolFormatter, DateFormatter, NumberFormatter
from ohmyadmin.helpers import LazyURL
from ohmyadmin.pages.form import FormPage
from ohmyadmin.pages.table import TablePage
from ohmyadmin.views.table import TableColumn


async def echo_action(request: Request) -> Response:
    return ActionResponse().show_toast(f'Clicked! Method: {request.method}')


async def refresh_page_action(request: Request) -> Response:
    return ActionResponse().show_toast(f'Clicked! Method: {request.method}').refresh()


async def handle_modal_form(request: Request, form: wtforms.Form) -> ActionResponse:
    return ActionResponse().show_toast('Form submitted.').close_modal()


async def toggle_visibility(request: Request, object_ids: list[str]) -> Response:
    async with async_session() as session:
        for object_id in object_ids:
            await session.execute(
                sa.update(Product).where(Product.id == int(object_id)).values(visible=~Product.visible)
            )
        await session.commit()
    return ActionResponse().show_toast('Visibility has been changed.').refresh_datatable()


async def delete_product_action(request: Request, object_ids: list[str]) -> Response:
    async with async_session() as session:
        for object_id in object_ids:
            product = await session.get(Product, int(object_id))
            await session.delete(product)
        await session.commit()
    return ActionResponse().show_toast('Product has been deleted.').refresh_datatable()


def product_name_validator(form, field):
    if field.data == 'fail':
        raise wtforms.ValidationError('Product name is invalid.')


class EditProductForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required(), product_name_validator])
    price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    compare_at_price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    sku = wtforms.IntegerField(default=0)
    quantity = wtforms.IntegerField(default=0)
    barcode = wtforms.StringField(default='')
    visible = wtforms.BooleanField(default=False)


class EditProductAction(actions.Modal):
    title = 'Edit product'

    async def dispatch(self, request: Request) -> Response:
        async with async_session() as session:
            object_id = request.query_params.get('_ids')
            model = None
            if object_id:
                result = await session.scalars(sa.select(Product).where(Product.id == int(object_id)))
                model = result.one()
            form = EditProductForm(await request.form(), obj=model)
            if request.method == 'POST' and form.validate():
                form.populate_obj(model)
                await session.commit()
                return ActionResponse().show_toast('Product has been updated.').refresh_datatable().close_modal()
            return self.render(request, {'form': form})


async def update_product(request: Request, form: wtforms.Form, object_ids: list[str]) -> Response:
    result = await request.state.db.scalars(sa.select(Product).where(Product.id == int(object_ids.pop())))
    instance = result.one()
    form.populate_obj(instance)
    await request.state.db.commit()
    return ActionResponse().show_toast('Product has been updated.').refresh_datatable().close_modal()


class MassDeleteAction(BaseBatchAction):
    dangerous = True
    label = 'Mass delete'
    message = 'Do you really want to apply mass delete action?'

    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        return ActionResponse().show_toast(f'Mass deleted {len(object_ids)} objects.').close_modal()


class MassMailAction(BaseBatchAction):
    class MassDeleteForm(wtforms.Form):
        subject = wtforms.StringField()
        message = wtforms.TextAreaField()

    label = 'Mass mail'
    form_class = MassDeleteForm
    message = 'Do you really want to sent messages to selected users?'

    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        return ActionResponse().show_toast(f'Mass mailed {len(object_ids)} objects. Data: {form.data}.').close_modal()


class CreateProductPage(FormPage):
    label = 'Create Product'
    form_class = EditProductForm
    datasource = SQLADataSource(Product, async_session)
    form_actions = [actions.Submit('Submit', variant='primary'), actions.Link('Back', '/')]


class ProductPage(TablePage):
    label = 'Product'
    datasource = SQLADataSource(Product, async_session, sa.select(Product).order_by(Product.created_at.desc()))
    page_actions = [
        actions.Callback('modal', 'New product', EditProductAction(), icon='window-maximize'),
        actions.Callback('refresh', 'Refresh page', refresh_page_action, 'refresh'),
        actions.Callback('click', 'Show toast', echo_action, 'hand-finger', color='success'),
        actions.Link('Add new', '/admin/product', icon='plus', variant='accent'),
    ]
    object_actions = [
        actions.ObjectLink(label='No icon', url='/'),
        actions.ObjectLink(label='Go to homepage', url='/', icon='link'),
        actions.ObjectLink(label='Go to homepage (route)', url=LazyURL(path_name='ohmyadmin.welcome'), icon='home'),
        actions.ObjectLink(
            label='For object', url=lambda r, o: r.url.include_query_params(obj=o.id), icon='accessible'
        ),
        actions.ObjectCallback('visibility', 'Toggle visibility', toggle_visibility, 'eye', method='post'),
        actions.ObjectCallback('edit', 'Edit', EditProductAction(), icon='pencil'),
        actions.ObjectCallback(
            'delete', 'Delete', delete_product_action, 'trash', method='delete', confirmation='Delete?', dangerous=True
        ),
    ]
    batch_actions = [
        actions.BatchAction(MassDeleteAction()),
        actions.BatchAction(MassMailAction()),
    ]
    columns = [
        TableColumn('name'),
        TableColumn('price', sortable=True, formatter=NumberFormatter(suffix='USD')),
        TableColumn('compare_at_price', sortable=True, formatter=NumberFormatter(suffix='USD')),
        TableColumn('sku', sortable=True, label='SKU', formatter=NumberFormatter()),
        TableColumn('quantity', sortable=True, label='Qty.', formatter=NumberFormatter()),
        TableColumn('barcode', searchable=True),
        TableColumn('visible', sortable=True, formatter=BoolFormatter(as_text=True)),
        TableColumn('availability', sortable=True, formatter=DateFormatter()),
        TableColumn('created_at', sortable=True, formatter=DateFormatter()),
    ]
    filters = [
        StringFilter('name'),
        DecimalFilter('price'),
        FloatFilter('compare_at_price'),
        IntegerFilter('sku'),
        DateFilter('created_at'),
        DateRangeFilter('created_at'),
        ChoiceFilter(
            'barcode',
            label='Bar code',
            choices=[
                ('0686594913423', 'Code 1'),
                ('0616403740810', 'Code 2'),
            ],
        ),
        MultiChoiceFilter(
            'quantity',
            choices=[
                (5, 'Five'),
                (15, 'Fifteen'),
            ],
            coerce=int,
        ),
    ]
