# project-related
from ..db import db


class StoreModel(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    address = db.Column(db.String(128))
    owner_id = db.Column(db.Integer(), db.ForeignKey("users.id"), nullable=False)
    owner = db.relationship("UserModel", back_populates="stores")
    vehicles = db.relationship("VehicleModel", back_populates="store", lazy="dynamic")

    def is_owner(self, user):
        return user.id == self.owner_id
