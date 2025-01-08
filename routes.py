from flask import render_template, request, redirect, url_for, jsonify, Response
from flask_login import login_user, logout_user, current_user, login_required
import json, os
from datetime import datetime

from models import User, Patient, PatientRecord, AcupuncturePoint
def get_domain_url():
    try:
        with open("secret.txt", "r") as file:
            return file.read().strip()  # Remove any trailing newline or spaces
    except FileNotFoundError:
        raise Exception("secret.txt not found. Please add it to the root directory.")


domain_url = get_domain_url()


def register_routes(app, db, bcrypt):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "GET":
            return render_template("signup.html")
        elif request.method == "POST":
            email = request.form.get("email")
            username = request.form.get("username")
            password = request.form.get("password")
            mobile_no = request.form.get("mobile_no")
            address = request.form.get("address")

            roles = request.form.getlist("role")

            if len(roles) == 2:
                role = "both"
            elif "admin" in roles:
                role = "admin"
            else:
                role = "therapists"

            hashed_password = bcrypt.generate_password_hash(password)

            user = User(
                email=email,
                username=username,
                password=hashed_password,
                mobile_no=mobile_no,
                address=address,
                role=role,
            )

            db.session.add(user)
            db.session.commit()
            return redirect(url_for("index"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        elif request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            user = User.query.filter(User.username == username).first()

            if user is None:
                return jsonify({"status": "failed", "message": "User not found"}), 404

            if bcrypt.check_password_hash(user.password, password):
                login_user(user)

                # Convert role string into a list
                role_mapping = {
                    "admin": ["admin"],
                    "therapist": ["therapist"],
                    "both": ["admin", "therapist"],
                }
                roles_as_list = role_mapping.get(user.role, [])

                user_data = {
                    "status": "success",
                    "user": {
                        "id": user.uid,
                        "profile_picture": f"{domain_url}/static/profile_pictures/picture1.jpg",
                        "username": user.username,
                        "email": user.email,
                        "mobile_no": user.mobile_no,
                        "address": user.address,
                        "role": roles_as_list,  # Return as a list
                    },
                }
                return jsonify(user_data), 200
            else:
                return jsonify({"status": "failed", "message": "Invalid password"}), 401

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route("/secret")
    @login_required
    def secret():
        return "My secret message"

    @app.route("/export-users", methods=["GET"])
    def export_users():
        try:
            users = User.query.all()

            role_mapping = {
                "admin": ["admin"],
                "therapist": ["therapist"],
                "both": ["admin", "therapist"],
            }

            user_list = [
                {
                    "id": user.uid,
                    "profile_picture": f"{domain_url}/static/profile_pictures/picture1.jpg",
                    "username": user.username,
                    "email": user.email,
                    "password": user.password,
                    "mobile_no": user.mobile_no,
                    "address": user.address,
                    "role": role_mapping.get(user.role, []),  # Convert role to a list
                }
                for user in users
            ]

            response = Response(
                json.dumps(user_list, ensure_ascii=False, indent=4),
                mimetype="application/json",
            )
            return response
        except Exception as e:
            return f"An error occurred: {str(e)}", 500


    @app.route("/register-patient", methods=["POST"])
    def register_patient():
        try:
            # Extract data from form
            name = request.form.get("name")
            mykad = request.form.get("mykad")
            gender = request.form.get("gender")
            ethnicity = request.form.get("ethnicity")
            p_mobile_no = request.form.get("p_mobile_no")
            p_email = request.form.get("p_email")
            postcode = request.form.get("postcode")
            state = request.form.get("state")
            address = request.form.get("address")
            occupation = request.form.get("occupation")
            medical_history = request.form.getlist("medical_history")  # Handles multiple values for a form field

            # Validate required fields
            required_fields = ["name", "mykad", "gender", "ethnicity", "p_mobile_no", "p_email", "postcode", "state", "address", "occupation"]
            missing_fields = [field for field in required_fields if not request.form.get(field)]
            if missing_fields:
                return jsonify({"status": "failed", "message": f"Missing fields: {', '.join(missing_fields)}"}), 400

            # Validate medical history (optional, ensure it's a list)
            if not isinstance(medical_history, list):
                return jsonify({"status": "failed", "message": "Medical history must be a list"}), 400

            # Create and save the patient
            patient = Patient(
                name=name,
                mykad=mykad,
                gender=gender,
                ethnicity=ethnicity,
                p_mobile_no=p_mobile_no,
                p_email=p_email,
                postcode=postcode,
                state=state,
                address=address,
                occupation=occupation,
                medical_history=json.dumps(medical_history),  # Convert list to JSON string
            )

            db.session.add(patient)
            db.session.commit()

            return jsonify({"status": "success", "message": "Patient registered successfully"}), 201

        except Exception as e:
            return jsonify({"status": "failed", "message": str(e)}), 500

    @app.route("/export-patients", methods=["GET"])
    def export_patients():
        try:
            # Retrieve all patients from the database
            patients = Patient.query.all()

            # Create a list of patient dictionaries
            patient_list = [
                {
                    "id": patient.pid,
                    "name": patient.name,
                    "mykad": patient.mykad,
                    "gender": patient.gender,
                    "ethnicity": patient.ethnicity,
                    "p_mobile_no": patient.p_mobile_no,
                    "p_email": patient.p_email,
                    "postcode": patient.postcode,
                    "state": patient.state,
                    "address": patient.address,
                    "occupation": patient.occupation,
                    "medical_history": json.loads(patient.medical_history) if patient.medical_history else [],  # Convert JSON string to list
                }
                for patient in patients
            ]

            # Create a JSON response
            response = Response(
                json.dumps(patient_list, ensure_ascii=False, indent=4),
                mimetype="application/json",
            )
            return response

        except Exception as e:
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

    @app.route('/submit-treatment', methods=['POST'])
    def submit_treatment():
        try:
            # Parse data from the request
            data = request.get_json()

            # Extract treatment details
            patient_id = data.get('patient_id')
            therapist_id = data.get('therapist_id')
            created_date = data.get('created_date')
            frequency = data.get('frequency')
            blood_pressure_before = data.get('blood_pressure_before')
            blood_pressure_after = data.get('blood_pressure_after')
            package = data.get('package')
            health_complications = data.get('health_complications')
            comments = data.get('comments')
            acupuncture_points = data.get('acupuncture_point')

            # Validate required fields
            if not all([patient_id, therapist_id, created_date, frequency, blood_pressure_before, blood_pressure_after, package]):
                return jsonify({'error': 'Missing required fields'}), 400

            # Create and commit the PatientRecord
            patient_record = PatientRecord(
                date=datetime.strptime(created_date, '%Y-%m-%d'),
                frequency=frequency,
                blood_pressure_before=blood_pressure_before,
                blood_pressure_after=blood_pressure_after,
                package=package,
                health_complications=health_complications or '',
                comments=comments or '',
                patient_id=patient_id,
                therapist_id=therapist_id
            )
            db.session.add(patient_record)
            db.session.flush()  # Flush to get the record_id for relationships

            # Create and commit the AcupuncturePoint records
            if acupuncture_points:
                for point in acupuncture_points:
                    body_part, coordinate_x, coordinate_y, skin_reaction, blood_quantity = point
                    acupuncture_point = AcupuncturePoint(
                        body_part=body_part,
                        coordinate_x=coordinate_x,
                        coordinate_y=coordinate_y,
                        skin_reaction=skin_reaction,
                        blood_quantity=blood_quantity,
                        record_id=patient_record.record_id
                    )
                    db.session.add(acupuncture_point)

            # Commit all changes
            db.session.commit()

            return jsonify({'message': 'Treatment data submitted successfully'}), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route("/insert-data", methods=["GET"])
    def insert_data():
        hashed_password_1= bcrypt.generate_password_hash("rehsoz")
        user1 = User(
            email="rehsoz@gmail.com",
            username="rehsoz",
            password=hashed_password_1,
            mobile_no="123456789",
            address="Gogai Street",
            role="therapists"
        )
        
        hashed_password_2= bcrypt.generate_password_hash("mendow")
        user2 = User(
            email="mendow@gmail.com",
            username="mendow",
            password=hashed_password_2,
            mobile_no="123456789",
            address="Mendow Street",
            role="admin"
        )

        hashed_password_3= bcrypt.generate_password_hash("testingBot")
        user3 = User(
            email="testingBot@gmail.com",
            username="testingBot",
            password=hashed_password_3,
            mobile_no="123456789",
            address="CCK Street",
            role="both"
        )

        patient1 = Patient(
            name="John Doe",
            mykad="123456789012",
            gender="Male",
            ethnicity="Malay",
            p_mobile_no="1234567890",
            p_email="johndoe@example.com",
            postcode="12345",
            state="Selangor",
            address="123 Patient Street",
            occupation="Engineer",
            medical_history="Diabetes, Hypertension",
            treatment_history="Acupuncture therapy in 2022"
        )

        record1 = PatientRecord(
            date=datetime.now(),
            frequency="3",
            blood_pressure_before="120/80",
            blood_pressure_after="118/78",
            package="Standard",
            health_complications="Mild headache",
            comments="Patient responded well",
            patient_id=1,  # Assuming this matches the patient primary key
            therapist_id=3  # Assuming this matches the user primary key
        )

        point1 = AcupuncturePoint(
            body_part="Front",
            coordinate_x=10,
            coordinate_y=20,
            skin_reaction=2,
            blood_quantity=5,
            record_id=1  # Assuming this matches the patient record primary key
        )

        db.session.add_all([user1, user2, user3, patient1])
        db.session.commit()

        db.session.add(record1)
        db.session.commit()

        db.session.add(point1)
        db.session.commit()
        return redirect(url_for("index"))

