import os
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, RedirectResponse, Response
from starlette.types import Receive, Scope, Send

from ohmyadmin.storage import FileStorage, InvalidFile, NotSupported


class MediaServer:
    def __init__(self, storage: FileStorage) -> None:
        self.storage = storage

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "http"

        if scope["method"] not in ("GET", "HEAD"):
            raise HTTPException(status_code=405)

        file_path = os.path.normpath(os.path.join(*scope["path"].split("/")))
        response = await self.get_response(file_path)
        await response(scope, receive, send)

    async def get_response(self, file_path: str) -> Response:
        try:
            # s3 or other online storages
            media_url = await self.storage.get_url(file_path)
            assert media_url.startswith('http://') or media_url.startswith(
                'https://'
            ), "Media URL must start with http:// or https://"
            return RedirectResponse(media_url, 302)
        except NotSupported:
            pass

        try:
            # local disk storage
            full_path = await self.storage.get_local_file_path(file_path)
            return FileResponse(full_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail='Media file not found.')
        except InvalidFile:
            raise HTTPException(status_code=403, detail='Media file could not be read.')
