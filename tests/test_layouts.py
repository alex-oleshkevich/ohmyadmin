import wtforms
from starlette.requests import Request

from ohmyadmin import layouts
from ohmyadmin.testing import MarkupSelector


def test_grid_layout(http_request: Request) -> None:
    layout = layouts.Grid(children=[layouts.Text('CONTENT')], columns=2, gap=5)

    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text('.grid-layout.md\\:grid-cols-2.gap-5') == 'CONTENT'


def test_column_layout(http_request: Request) -> None:
    layout = layouts.Column(children=[layouts.Text('CONTENT')], gap=5, colspan=5)

    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text('.column-layout.col-span-5') == 'CONTENT'
    assert selector.has_node('.column-layout .grid.grid-cols-1.gap-5')


def test_row_layout(http_request: Request) -> None:
    layout = layouts.Row(children=[layouts.Text('CONTENT')], gap=5)

    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text('.row-layout.flex.flex-row.gap-5') == 'CONTENT'


def test_card_layout(http_request: Request) -> None:
    layout = layouts.Card(children=[layouts.Text('CONTENT')], label='TITLE', description='DESCRIPTION')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text('.card header h3') == 'TITLE'
    assert selector.get_text('.card header p') == 'DESCRIPTION'
    assert selector.get_text('.card main') == 'CONTENT'


def test_card_layout_no_description(http_request: Request) -> None:
    layout = layouts.Card(children=[layouts.Text('CONTENT')], label='TITLE')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node('.card header h3')
    assert not selector.has_node('.card header p')


def test_card_layout_no_label(http_request: Request) -> None:
    layout = layouts.Card(children=[layouts.Text('CONTENT')], description='TITLE')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node('.card header p')
    assert not selector.has_node('.card header h3')


def test_card_layout_no_label_and_no_description(http_request: Request) -> None:
    layout = layouts.Card(children=[layouts.Text('CONTENT')])
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert not selector.has_node('.card header')


def test_side_section_layout(http_request: Request) -> None:
    layout = layouts.SideSection(children=[layouts.Text('CONTENT')], label='TITLE', description='DESCRIPTION')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text('.side-section aside h3') == 'TITLE'
    assert selector.get_text('.side-section aside p') == 'DESCRIPTION'
    assert selector.get_text('.side-section main') == 'CONTENT'


def test_side_section_no_description(http_request: Request) -> None:
    layout = layouts.SideSection(children=[layouts.Text('CONTENT')], label='TITLE')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node('.side-section aside h3')
    assert not selector.has_node('.side-section aside p')


def test_input_layout(http_request: Request) -> None:
    class MyForm(wtforms.Form):
        name = wtforms.StringField()

    form = MyForm()
    layout = layouts.Input(form.name, max_width='lg', colspan=3)
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node('.input-layout.max-w-lg.col-span-3')
    assert selector.has_node('.input-layout input[name="name"]')


def test_row_form_layout(http_request: Request) -> None:
    class MyForm(wtforms.Form):
        name = wtforms.StringField()

    form = MyForm()
    layout = layouts.RowFormLayout(children=[layouts.Input(form.name)], label='TITLE', description='DESCRIPTION')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text('.row-form-layout header h3') == 'TITLE'
    assert selector.get_text('.row-form-layout header p') == 'DESCRIPTION'
    assert selector.has_node('.row-form-layout main input[name="name"]')


def test_row_form_layout_no_description(http_request: Request) -> None:
    class MyForm(wtforms.Form):
        name = wtforms.StringField()

    form = MyForm()
    layout = layouts.RowFormLayout(children=[layouts.Input(form.name)], label='TITLE')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node('.row-form-layout header h3')
    assert not selector.has_node('.row-form-layout header p')


def test_stacked_form_layout(http_request: Request) -> None:
    class MyForm(wtforms.Form):
        name = wtforms.StringField()

    form = MyForm()
    layout = layouts.StackedForm(children=[layouts.Input(form.name)], label='TITLE', description='DESCRIPTION')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text('.stacked-form header h3') == 'TITLE'
    assert selector.get_text('.stacked-form header p') == 'DESCRIPTION'
    assert selector.has_node('.stacked-form main input[name="name"]')


def test_stacked_form_layout_no_description(http_request: Request) -> None:
    class MyForm(wtforms.Form):
        name = wtforms.StringField()

    form = MyForm()
    layout = layouts.StackedForm(children=[layouts.Input(form.name)], label='TITLE')
    content = layout.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node('.stacked-form header h3')
    assert not selector.has_node('.stacked-form header p')


def test_text(http_request: Request) -> None:
    layout = layouts.Text('CONTENT')
    assert layout.render(http_request) == 'CONTENT'
