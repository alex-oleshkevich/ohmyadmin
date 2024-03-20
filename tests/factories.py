import polyfactory.factories

from tests.models import User


class UserFactory(polyfactory.factories.DataclassFactory[User]):
    email = polyfactory.factories.DataclassFactory.__faker__.email()
    password = "password"
    __model__ = User
