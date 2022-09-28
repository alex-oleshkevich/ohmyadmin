from ohmyadmin.resources import Resource


class DemoModelResource(Resource):
    ...


def test_generates_slug() -> None:
    assert DemoModelResource.slug == 'demo-models'


def test_generates_label() -> None:
    assert DemoModelResource.label == 'Demo Model'


def test_generates_plural_label() -> None:
    assert DemoModelResource.label_plural == 'Demo Models'


def test_url_name() -> None:
    assert DemoModelResource.url_name('edit') == 'ohmyadmin.demo_models.edit'
