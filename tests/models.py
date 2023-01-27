import dataclasses

import datetime
from starlette.authentication import BaseUser


@dataclasses.dataclass
class User(BaseUser):
    id: str
    is_authenticated: bool = True
    display_name: str = 'User'

    @property
    def identity(self) -> str:
        return self.id


@dataclasses.dataclass
class Post:
    id: int = 1
    title: str = 'Title'
    published: bool = False
    date_published: datetime.date = dataclasses.field(default_factory=lambda: datetime.datetime.today().date())
    updated_at: datetime.date = dataclasses.field(default_factory=lambda: datetime.datetime.today())

    def __str__(self) -> str:
        return self.title
