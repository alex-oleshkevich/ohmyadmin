import abc
import anyio
import os.path
import pathlib
from starlette.datastructures import UploadFile


class FileStorage:
    @abc.abstractmethod
    async def write(self, path: str | os.PathLike, stream: UploadFile) -> pathlib.Path:
        ...


class LocalDirectoryStorage(FileStorage):
    def __init__(self, directory: str | os.PathLike, url_prefix: str = '/') -> None:
        if str(directory).startswith('.'):
            raise ValueError('Directory must be absolute path.')

        self.url_prefix = url_prefix
        self.directory = pathlib.Path(directory)
        os.makedirs(directory, exist_ok=True)

    async def write(self, path: str | os.PathLike, file: UploadFile) -> pathlib.Path:
        abs_path = self.directory / path
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        async with await anyio.open_file(abs_path, 'wb') as f:
            while chunk := await file.read(8096):
                await f.write(chunk)
        return abs_path
