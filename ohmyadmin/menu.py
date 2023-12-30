from __future__ import annotations

import dataclasses

from starlette.datastructures import URL


@dataclasses.dataclass
class MenuItem:
    label: str
    group: str = ""
    icon: str = ""
    url: URL | None = None
    children: list[MenuItem] | None = None
