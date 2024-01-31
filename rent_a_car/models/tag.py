# project-related
from ..db import db


class TagModel(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    categories = db.relationship(
        "CategoryModel", back_populates="tags", secondary="category_tags"
    )
    models = db.relationship(
        "ModelModel", back_populates="tags", secondary="model_tags"
    )


class CategoryTagModel(db.Model):
    __tablename__ = "category_tags"

    id = db.Column(db.Integer(), primary_key=True)
    tag_id = db.Column(db.Integer(), db.ForeignKey("tags.id"), nullable=False)
    category_id = db.Column(
        db.Integer(), db.ForeignKey("categories.id"), nullable=False
    )


class ModelTagModel(db.Model):
    __tablename__ = "model_tags"

    id = db.Column(db.Integer(), primary_key=True)
    tag_id = db.Column(db.Integer(), db.ForeignKey("tags.id"), nullable=False)
    model_id = db.Column(db.Integer(), db.ForeignKey("models.id"), nullable=False)
