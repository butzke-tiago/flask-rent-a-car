# project-related
from ..db import db


class CategoryModel(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    fare = db.Column(db.Float(), nullable=False, default=100.0)
    models = db.relationship("ModelModel", back_populates="category", lazy="dynamic")
