from flask_login import UserMixin
from app import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    mobile_no = db.Column(db.String(12), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def get_id(self):
        return self.uid

class Patient(db.Model):
    __tablename__ = "patients"

    pid = db.Column(db.Integer, primary_key=True)
    p_name = db.Column(db.String(100), unique=True, nullable=False)

