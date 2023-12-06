import pytest
from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.helpers import (
    LazyObjectURL,
    LazyURL,
    camel_to_sentence,
    get_callable_name,
    pluralize,
    resolve_url,
    snake_to_sentence,
)


def test_camel_to_sentence() -> None:
    assert camel_to_sentence("CamelCase") == "Camel case"
    assert camel_to_sentence("camelCase") == "Camel case"


def test_snake_to_sentence() -> None:
    assert snake_to_sentence("snake_case") == "Snake case"


def test_pluralize() -> None:
    assert pluralize("apple") == "apples"
    assert pluralize("category") == "categories"
    assert pluralize("service") == "services"
    assert pluralize("boss") == "bosses"
    assert pluralize("categories") == "categories"
    assert pluralize("wheat") == "wheat"


def test_lazy_url(http_request: Request) -> None:
    url = LazyURL(path_name="users")
    assert str(url.resolve(http_request)) == "http://testserver/admin/users"

    url = LazyURL(path_name="posts", path_params={"id": 100})
    assert str(url.resolve(http_request)) == "http://testserver/admin/posts/100"


def test_lazy_object_url(http_request: Request) -> None:
    url = LazyObjectURL(lambda r, o: URL("/users"))
    assert str(url.resolve(http_request, object())) == "/users"


def test_resolve_url(http_request: Request) -> None:
    assert str(resolve_url(http_request, "/users")) == "/users"
    assert str(resolve_url(http_request, URL("/users"))) == "/users"
    assert (
        str(resolve_url(http_request, LazyURL("users")))
        == "http://testserver/admin/users"
    )
    assert (
        str(resolve_url(http_request, LazyURL("posts", {"id": 100})))
        == "http://testserver/admin/posts/100"
    )


def _example_function() -> None:  # pragma: no cover
    ...


class SomeClass:  # pragma: no cover
    def some_method(self) -> None:
        ...


def test_get_callable_name(http_request: Request) -> None:
    assert get_callable_name(_example_function) == "_example_function"
    assert get_callable_name(SomeClass) == "SomeClass"
    assert get_callable_name(SomeClass.some_method) == "some_method"
    assert get_callable_name(SomeClass().some_method) == "some_method"

    with pytest.raises(ValueError, match="Unsupported"):
        assert get_callable_name(1)
