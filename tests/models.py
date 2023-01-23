import dataclasses

from starlette.authentication import BaseUser


@dataclasses.dataclass
class User(BaseUser):
    id: str
    is_authenticated: bool = True
    display_name: str = 'User'

    @property
    def identity(self) -> str:
        return self.id
