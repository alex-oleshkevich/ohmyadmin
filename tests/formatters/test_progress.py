from starlette.requests import Request

from ohmyadmin.formatters import ProgressFormatter
from ohmyadmin.testing import MarkupSelector


def test_progress_default_settings(http_request: Request) -> None:
    formatter = ProgressFormatter()
    content = formatter.format(http_request, 42)
    selector = MarkupSelector(content)
    assert selector.has_node('.progress.progress-sm')
    assert selector.has_node('.progress.progress-accent')


def test_progress_size(http_request: Request) -> None:
    formatter = ProgressFormatter(size='lg')
    content = formatter.format(http_request, 42)
    selector = MarkupSelector(content)
    assert selector.has_node('.progress.progress-lg')


def test_progress_color(http_request: Request) -> None:
    formatter = ProgressFormatter(color='red')
    content = formatter.format(http_request, 42)
    selector = MarkupSelector(content)
    assert selector.has_node('.progress.progress-red')


def test_progress_label(http_request: Request) -> None:
    formatter = ProgressFormatter(label='Progress')
    content = formatter.format(http_request, 42)
    selector = MarkupSelector(content)
    assert selector.has_node('.progress-label')
    assert selector.get_text('.progress-label dt') == 'Progress'
    assert selector.get_text('.progress-label dd') == '42%'


def test_progress_nolabel(http_request: Request) -> None:
    formatter = ProgressFormatter()
    content = formatter.format(http_request, 42)
    selector = MarkupSelector(content)
    assert not selector.has_node('.progress-label')
