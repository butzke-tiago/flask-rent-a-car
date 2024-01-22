# flask-related
from flask_login import UserMixin

# project-related
from ..db import db


class UserModel(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), unique=True)
    password = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    role = db.Column(db.Integer, nullable=False)
