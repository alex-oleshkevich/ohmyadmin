import inspect
import os
import pathlib
import typing

from starlette.responses import FileResponse, Response


class StorageError(Exception):
    ...


class AsyncReader(typing.Protocol):
    async def read(self, n: int) -> bytes:
        ...


class FileStorage(typing.Protocol):
    async def read(self, path: str) -> bytes:
        ...

    async def delete(self, path: str) -> None:
        ...

    async def write(self, path: str, data: bytes | typing.IO[bytes] | AsyncReader) -> None:
        ...

    async def url(self, path: str) -> str:
        ...

    def as_response(self, path: str) -> Response:
        ...


class FileSystemStorage:
    def __init__(
        self,
        directory: str | os.PathLike,
        url_prefix: str = "",
    ) -> None:
        self.url_prefix = url_prefix
        self.directory: pathlib.Path = pathlib.Path(directory)

    def as_response(self, path: str) -> Response:
        return FileResponse(self.directory / path)

    async def read(self, path: str) -> bytes:
        return (self.directory / path).read_bytes()

    async def delete(self, path: str) -> None:
        os.remove(self.directory / path)

    async def write(self, path: str, data: bytes | typing.IO[bytes] | AsyncReader) -> None:
        requested_dir = os.path.dirname(path)
        if requested_dir.startswith(".."):
            raise StorageError("Writing to parent directories is not allowed.")

        destination = self.directory / path
        destination.parent.mkdir(0o755, exist_ok=True, parents=True)

        if isinstance(data, bytes):
            destination.write_bytes(data)
            return

        reader = getattr(data, "read", None)
        if reader is None:
            raise StorageError("Invalid source type.")

        with destination.open("wb") as outf:
            if inspect.iscoroutinefunction(reader):
                while chunk := await reader(1024 * 128):
                    outf.write(chunk)
                return

            while chunk := data.read(1024 * 128):
                outf.write(chunk)


async def url(self, path: str) -> str:
    return self.url_prefix.rstrip("/") + "/" + path
