import re


def camel_to_sentence(text: str) -> str:
    """
    Convert camel cased strings (like class names) into a sentence.

    Example: OrderItemsResource -> Order items resource.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text)


def snake_to_sentence(text: str) -> str:
    return text.replace('_', ' ')


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
