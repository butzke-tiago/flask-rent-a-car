# project-related
from ..db import db, get_entry, get_entry_by, get_entries_filtered
from ..models import UserModel

# misc
from enum import Enum
from sqlalchemy.exc import SQLAlchemyError
from passlib.hash import pbkdf2_sha256


class DuplicateUserError(Exception):
    pass


class UserRole(Enum):
    ADMIN = 0
    FRANCHISEE = 1
    CLIENT = 2


class UserService:
    def register(self, role: UserRole, email: str, password: str, name: str):
        if get_entries_filtered(UserModel, email=email):
            raise DuplicateUserError(
                f"The email {email!r} is already associated with an user!"
            )
        user = UserModel(
            role=role.value,
            email=email,
            password=pbkdf2_sha256.hash(password),
            name=name,
        )
        try:
            db.session.add(user)
            db.session.commit()
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


service = UserService()
