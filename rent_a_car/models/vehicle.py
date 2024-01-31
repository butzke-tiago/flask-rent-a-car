# project-related
from ..db import db


class VehicleModel(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(8), unique=True, nullable=False)
    model_id = db.Column(db.Integer(), db.ForeignKey("models.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    store_id = db.Column(db.Integer(), db.ForeignKey("stores.id"))

    model = db.relationship("ModelModel", back_populates="vehicles")
    store = db.relationship("StoreModel", back_populates="vehicles")
