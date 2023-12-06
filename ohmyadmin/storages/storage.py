import pathlib
import typing


class FileStorage(typing.Protocol):
    async def read(self, path: str) -> bytes:
        ...

    async def write(self, path: str, data: bytes) -> None:
        ...

    async def url(self, path: str) -> str:
        ...


class FileSystemStorage:
    def __init__(
        self,
        directory: str | pathlib.Path,
        url_prefix: str = "",
    ) -> None:
        self.url_prefix = url_prefix
        self.directory: pathlib.Path = pathlib.Path(directory)

    async def read(self, path: str) -> bytes:
        return (self.directory / path).read_bytes()

    async def write(self, path: str, data: bytes) -> None:
        (self.directory / path).write_bytes(data)

    async def url(self, path: str) -> str:
        return self.url_prefix.rstrip("/") + "/" + path
