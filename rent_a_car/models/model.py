# project-related
from ..db import db


class ModelModel(db.Model):
    __tablename__ = "models"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    make_id = db.Column(db.Integer(), db.ForeignKey("makes.id"), nullable=False)
    category_id = db.Column(
        db.Integer(), db.ForeignKey("categories.id"), nullable=False
    )
    picture = db.Column(db.String())
    make = db.relationship("MakeModel", back_populates="models")
    category = db.relationship("CategoryModel", back_populates="models")
    vehicles = db.relationship("VehicleModel", back_populates="model", lazy="dynamic")
