import dataclasses
import datetime

from starlette.authentication import BaseUser


@dataclasses.dataclass
class User(BaseUser):
    id: int
    first_name: str
    last_name: str
    email: str
    is_active: bool
    birthdate: datetime.date
