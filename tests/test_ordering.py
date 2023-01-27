from ohmyadmin.ordering import SortingHelper, get_ordering_value
from tests.conftest import RequestFactory


def test_extracts_ordering_from_query(request_f: RequestFactory) -> None:
    request = request_f(query_string='')
    assert get_ordering_value(request, 'ordering') == {}

    request = request_f(query_string='ordering=title')
    assert get_ordering_value(request, 'ordering') == {'title': 'asc'}

    request = request_f(query_string='ordering=-title')
    assert get_ordering_value(request, 'ordering') == {'title': 'desc'}

    request = request_f(query_string='ordering=-title&ordering=id')
    assert get_ordering_value(request, 'ordering') == {'title': 'desc', 'id': 'asc'}


def test_helper_returns_current_ordering(request_f: RequestFactory) -> None:
    request = request_f(query_string='ordering=title&ordering=-id')
    helper = SortingHelper(request, 'ordering')
    assert helper.get_current_ordering('title') == 'asc'
    assert helper.get_current_ordering('id') == 'desc'
    assert helper.get_current_ordering('name') is None


def test_helper_returns_current_ordering_index(request_f: RequestFactory) -> None:
    request = request_f(query_string='ordering=title&ordering=-id')
    helper = SortingHelper(request, 'ordering')
    assert helper.get_current_ordering_index('title') == 1
    assert helper.get_current_ordering_index('id') == 2
    assert helper.get_current_ordering_index('name') is None


def test_helper_generates_next_url(request_f: RequestFactory) -> None:
    request = request_f(query_string='')
    helper = SortingHelper(request, 'ordering')
    assert str(helper.get_url('title')) == 'http://testserver/admin/?ordering=title'


def test_helper_generates_next_url_inverted(request_f: RequestFactory) -> None:
    request = request_f(query_string='ordering=title')
    helper = SortingHelper(request, 'ordering')
    assert str(helper.get_url('title')) == 'http://testserver/admin/?ordering=-title'


def test_helper_generates_next_url_reset(request_f: RequestFactory) -> None:
    request = request_f(query_string='ordering=-title')
    helper = SortingHelper(request, 'ordering')
    assert str(helper.get_url('title')) == 'http://testserver/admin/'


def test_helper_generates_new_url_for_multiple_params(request_f: RequestFactory) -> None:
    request = request_f(query_string='ordering=title&ordering=-id')
    helper = SortingHelper(request, 'ordering')
    assert str(helper.get_url('title')) == 'http://testserver/admin/?ordering=-title&ordering=-id'


def test_helper_should_show_index(request_f: RequestFactory) -> None:
    request = request_f(query_string='ordering=title&ordering=-id')
    helper = SortingHelper(request, 'ordering')
    assert helper.should_show_index()

    request = request_f(query_string='ordering=title')
    helper = SortingHelper(request, 'ordering')
    assert not helper.should_show_index()

    request = request_f(query_string='')
    helper = SortingHelper(request, 'ordering')
    assert not helper.should_show_index()


def test_helper_generates_control(request_f: RequestFactory) -> None:
    request = request_f(query_string='ordering=title')
    helper = SortingHelper(request, 'ordering')
    control = helper.get_control('title')
    assert control.index == 1
    assert control.ordering == 'asc'
    assert str(control.url) == 'http://testserver/admin/?ordering=-title'
    assert control.show_index is False
