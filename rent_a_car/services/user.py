# project-related
from ..db import *
from ..models import UserModel, UserRole

# misc
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import SQLAlchemyError


class DuplicateUserError(Exception):
    pass


class UserService:
    def register(self, role: UserRole, email: str, password: str, name: str):
        if get_entries_filtered(UserModel, email=email):
            raise DuplicateUserError(
                f"The email {email!r} is already associated with an user!"
            )
        user = UserModel(
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
        return self.register(
            UserRole.FRANCHISEE, email=email, password=password, name=name
        )

    def register_client(self, email: str, password: str, name: str):
        return self.register(UserRole.CLIENT, email=email, password=password, name=name)

    def get_user(self, id):
        return get_entry(UserModel, id)

    def get_user_by_email(self, email):
        return get_entry_by(UserModel, email=email)

    def login(self, email: str, password: str):
        user = self.get_user_by_email(email)
        return user, user and pbkdf2_sha256.verify(password, user.password)

    def is_admin(self, user):
        return user.role == UserRole.ADMIN

    def is_franchisee(self, user):
        return user.role == UserRole.FRANCHISEE

    def is_client(self, user):
        return user.role == UserRole.CLIENT


service = UserService()
