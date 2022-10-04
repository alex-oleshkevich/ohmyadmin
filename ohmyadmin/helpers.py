from __future__ import annotations

import re

from ohmyadmin.globals import get_current_request


def camel_to_sentence(text: str) -> str:
    """
    Convert camel cased strings (like class names) into a sentence.

    Example: OrderItemsResource -> Order items resource.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text)


def snake_to_sentence(text: str) -> str:
    return text.replace('_', ' ')


def url(path_name: str, **path_params: str | int) -> str:
    return get_current_request().url_for(path_name, **(path_params or {}))


def media_url(path: str) -> str:
    return get_current_request().url_for('ohmyadmin_media', path=path)


def media_url_or_redirect(path: str) -> str:
    if path.startswith('http://') or path.startswith('https://'):
        return path
    return media_url(path)


def pluralize(text: str) -> str:
    """
    A simple pluralization utility.

    It adds -ies suffix to any noun that ends with -y, it adds -es suffix to any
    noun that ends with -s. For all other cases it appends -s.
    """
    if text.endswith('y'):
        return text[:-1] + 'ies'
    if text.endswith('s'):
        return text + 'es'
    return text + 's'
