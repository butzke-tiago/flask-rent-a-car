# flask-related
from flask_login import UserMixin

# project-related
from ..db import db

# misc
from enum import Enum


class UserRole(Enum):
    ADMIN = 0
    FRANCHISEE = 1
    CLIENT = 2


class UserModel(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), unique=True)
    password = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
    )
    stores = db.relationship("StoreModel", back_populates="owner", lazy="dynamic")
