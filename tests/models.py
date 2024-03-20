import dataclasses
import datetime

from starlette.authentication import BaseUser


@dataclasses.dataclass
class User(BaseUser):
    id: int = 1
    first_name: str = "John"
    last_name: str = "Doe"
    email: str = "john.doe@localhost"
    is_active: bool = True
    birthdate: datetime.date = datetime.date(1990, 1, 1)
    password: str = "password"

    @property
    def identity(self) -> str:
        return self.id

    @property
    def is_authenticated(self) -> bool:
        return True
