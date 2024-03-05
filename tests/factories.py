import polyfactory.factories

from tests.models import User


class UserFactory(polyfactory.factories.DataclassFactory[User]):
    __model__ = User
