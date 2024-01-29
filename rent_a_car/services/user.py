# project-related
from ..db import *
from ..models import UserModel, UserRole
from .base import BaseService, DuplicateError

# misc
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import SQLAlchemyError


class DuplicateUserError(DuplicateError):
    pass


class UserService(BaseService):
    def create(self, role: UserRole, email: str, password: str, name: str):
        if get_entries_filtered(self.model, email=email):
            raise DuplicateUserError(
                f"The email {email!r} is already associated with an user!"
            )
        user = self.model(
            role=role,
            email=email,
            password=pbkdf2_sha256.hash(password),
            name=name,
        )
        try:
            add_entry(user)
        except SQLAlchemyError:
            raise
        else:
            return user

    def register_franchisee(self, email: str, password: str, name: str):
        return self.create(
            UserRole.FRANCHISEE, email=email, password=password, name=name
        )

    def register_client(self, email: str, password: str, name: str):
        return self.create(UserRole.CLIENT, email=email, password=password, name=name)

    def get_by_email(self, email):
        return get_entry_by(self.model, email=email)

    def login(self, email: str, password: str):
        user = self.get_by_email(email)
        return user, user and pbkdf2_sha256.verify(password, user.password)


service = UserService("user", UserModel)
