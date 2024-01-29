# project-related
from ..db import db


class MakeModel(db.Model):
    __tablename__ = "makes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    logo = db.Column(db.String())
    models = db.relationship("ModelModel", back_populates="make", lazy="dynamic")
