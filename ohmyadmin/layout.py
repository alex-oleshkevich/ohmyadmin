import abc


class View(abc.ABC):
    @abc.abstractmethod
    def render(self) -> str:
        ...

    __call__ = render
    __str__ = render
