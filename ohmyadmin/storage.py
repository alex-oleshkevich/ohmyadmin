import abc
import anyio
import os.path
import pathlib
from starlette.datastructures import UploadFile


class NotSupported(Exception):
    ...


class FileStorage:
    @abc.abstractmethod
    async def write(self, path: str | os.PathLike, stream: UploadFile) -> pathlib.Path:
        ...

    async def get_url(self, path: str) -> str:
        raise NotSupported()

    def get_local_file_path(self, path: str) -> str:
        raise NotImplementedError(f'This method is not supported by {self.__class__.__name__}.')


class LocalDirectoryStorage(FileStorage):
    def __init__(self, directory: str | os.PathLike) -> None:
        if str(directory).startswith('.'):
            raise ValueError('Directory must be absolute path.')

        self.directory = pathlib.Path(directory)
        os.makedirs(directory, exist_ok=True)

    async def write(self, path: str | os.PathLike, file: UploadFile) -> pathlib.Path:
        abs_path = self.directory / path
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        async with await anyio.open_file(abs_path, 'wb') as f:
            while chunk := await file.read(8096):
                await f.write(chunk)
        return abs_path

    def get_local_file_path(self, path: str) -> str:
        full_path = os.path.join(self.directory, path)
        if not os.path.exists(full_path):
            raise FileNotFoundError('Media file does not exists.')
        return full_path
