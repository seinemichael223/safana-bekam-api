from flask_login import UserMixin
from sqlalchemy import NotNullable, Nullable, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import Float
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
    __tablename__ = "patients"  # Table for patients

    pid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    mykad = db.Column(db.String(50), unique=True, nullable=False)
    gender = db.Column(db.String(250), nullable=False)
    ethnicity = db.Column(db.String(40), nullable=False)
    p_mobile_no = db.Column(db.String(14), nullable=False)
    p_email = db.Column(db.String(150), nullable=False)
    postcode = db.Column(db.String(9), nullable=False)
    state = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    occupation = db.Column(db.String(80), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    # Relationship with MedicalHistory
    medical_histories = db.relationship('MedicalHistory', backref='patient', cascade="all, delete-orphan", lazy=True)

    def get_id(self):
        return self.pid


class MedicalHistory(db.Model):
    __tablename__ = "medical_history"  # Table for medical history

    id = db.Column(db.Integer, primary_key=True)
    condition = db.Column(db.String(100), nullable=False)
    medicine = db.Column(db.String(100), nullable=False)

    # Foreign key to link with the Patient
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.pid'), nullable=False)

    def get_id(self):
        return self.id

class PatientRecord(db.Model):
    __tablename__ = "patient_records"  # Table for patient records

    record_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    blood_pressure_before = db.Column(db.String(10), nullable=False)
    blood_pressure_after = db.Column(db.String(10), nullable=False)
    package = db.Column(db.String(80), nullable=False)
    health_complications = db.Column(db.String(200), nullable=False)
    comments = db.Column(db.String(500), nullable=False)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.pid'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('records', lazy=True))
    therapist = db.relationship('User', backref=db.backref('handled_records', lazy=True))

    def get_id(self):
        return self.record_id

class AcupuncturePoint(db.Model):
    __tablename__ = "acupuncture_point"  # Table for patient records

    point_id = db.Column(db.Integer, primary_key=True)
    body_part = db.Column(db.String(20), nullable=False)
    coordinate_x = db.Column(db.String(40), nullable=False)
    coordinate_y = db.Column(db.String(40), nullable=False)
    skin_reaction = db.Column(db.Integer, nullable=False)
    blood_quantity = db.Column(db.Integer, nullable=False)

    record_id = db.Column(db.Integer, db.ForeignKey('patient_records.record_id'), nullable=False)

    def get_id(self):
        return self.point_id

class Notifications(db.Model):
    __tablename__ = "notifications"  # Table for patient records

    notif_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    notif_type = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(60), nullable=False)


    def get_id(self):
        return self.notif_id
