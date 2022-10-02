import abc
import anyio
import os.path
import pathlib
import stat
from starlette.datastructures import UploadFile


class NotSupported(Exception):
    ...


class InvalidFile(Exception):
    ...


class FileStorage:
    @abc.abstractmethod
    async def write(self, path: str | os.PathLike, stream: UploadFile) -> str:
        ...

    @abc.abstractmethod
    async def delete(self, path: str | os.PathLike) -> None:
        ...

    async def get_url(self, path: str) -> str:
        raise NotSupported()

    async def get_local_file_path(self, path: str) -> str:
        raise NotImplementedError(f'This method is not supported by {self.__class__.__name__}.')


class LocalDirectoryStorage(FileStorage):
    def __init__(self, directory: str | os.PathLike) -> None:
        if str(directory).startswith('.'):
            raise ValueError('Directory must be absolute path.')

        self.directory = pathlib.Path(directory)
        os.makedirs(directory, exist_ok=True)

    async def write(self, path: str | os.PathLike, file: UploadFile) -> str:
        abs_path = self.directory / path
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        async with await anyio.open_file(abs_path, 'wb') as f:
            while chunk := await file.read(1024 * 8):
                await f.write(chunk)
        return str(path)

    async def delete(self, path: str | os.PathLike) -> None:
        abs_path = self.directory / path
        file_exists = await anyio.to_thread.run_sync(os.path.exists, abs_path)
        if file_exists:
            await anyio.to_thread.run_sync(os.remove, abs_path)

    async def get_local_file_path(self, path: str) -> str:
        """
        Get absolute file path for a given file.

        :raises InvalidFile
        :raises FileNotFoundError
        """

        try:
            full_path = os.path.join(self.directory, path)
            stat_result: os.stat_result = await anyio.to_thread.run_sync(os.stat, full_path)
        except OSError as ex:
            raise InvalidFile('Media file could not be read.') from ex

        if not stat_result:
            raise FileNotFoundError('Media file does not exists.')

        if stat.S_ISREG(stat_result.st_mode):
            return full_path

        raise InvalidFile('Do not know how to read file.')
