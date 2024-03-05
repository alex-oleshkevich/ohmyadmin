import datetime
import os.path
import time
import typing
import uuid

from async_storages import FileStorage
from starlette.datastructures import UploadFile
from starlette.requests import Request


async def upload_file(
    request: Request,
    file: UploadFile,
    destination: str,
    tokens: typing.Mapping[str, str] | None = None,
) -> str:
    storage: FileStorage = request.state.ohmyadmin.file_storage
    destination = destination.format(
        random=uuid.uuid4().hex[:8],
        name=os.path.splitext(file.filename or "unnamed")[0],
        extension=os.path.splitext(file.filename or "unnamed")[1].removeprefix("."),
        date=datetime.datetime.now().date().isoformat(),
        datetime=datetime.datetime.now().isoformat(),
        time=datetime.datetime.now().time().isoformat(),
        timestamp=int(time.time()),
        directory=os.path.dirname(destination),
        basename=file.filename,
        uuid=uuid.uuid4().hex,
        **(tokens or {}),
    )
    await storage.write(destination, file)
    return destination


async def delete_file(request: Request, path: str) -> None:
    storage: FileStorage = request.state.ohmyadmin.file_storage
    await storage.delete(path)
