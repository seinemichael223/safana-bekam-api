from flask import render_template, request, redirect, url_for, jsonify, Response, session
from flask_login import login_user, logout_user, current_user, login_required
import json, os
from datetime import datetime

from models import User, Patient, PatientRecord, AcupuncturePoint, MedicalHistory
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

                # Create session variables
                session.permanent = True
                session['username'] = user.username
                session['user_id'] = user.uid
                session['role'] = roles_as_list  # Store as a list

                user_data = {
                    "status": "success",
                    "user": {
                        "id": user.uid,
                        "profile_picture": f"{domain_url}/static/profile_pictures/picture1.jpg",
                        "username": user.username,
                        "email": user.email,
                        "mobile_no": user.mobile_no,
                        "address": user.address,
                        "role": roles_as_list,
                    },
                }
                return jsonify(user_data), 200
            else:
                return jsonify({"status": "failed", "message": "Invalid password"}), 401

    @app.route("/logout")
    def logout():
        logout_user()
        session.clear()  # Clear all session variables
        return redirect(url_for("index"))

    @app.route("/secret")
    def secret():
        # Check session variables
        if not session.get('user_id') or "admin" not in session.get('role', []):
            return jsonify({"status": "failed", "message": "Unauthorized access"}), 403
        return "My secret message"

    @app.route("/export-users", methods=["GET"])
    def export_users():
        try:

            if not session.get('user_id') or "admin" not in session.get('role', []):
                return jsonify({"status": "failed", "message": "Unauthorized access"}), 403
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


    # Register a Patient
    @app.route("/register-patient", methods=["GET", "POST"])
    def register_patient():
        if request.method == "GET":
            return render_template("register_patient.html")
        elif request.method == "POST":

            # if not session.get('user_id') or "admin" not in session.get('role', []):
            #     return jsonify({"status": "failed", "message": "Unauthorized access"}), 403

            try:
                # Parse JSON data from the request
                data = request.get_json()

                # Extract data using data.get
                name = data.get("name")
                mykad = data.get("mykad")
                gender = data.get("gender")
                ethnicity = data.get("ethnicity")
                p_mobile_no = data.get("p_mobile_no")
                p_email = data.get("p_email")
                postcode = data.get("postcode")
                state = data.get("state")
                address = data.get("address")
                occupation = data.get("occupation")
                medical_history = data.get("medical_history", [])  # Default to an empty list if not provided

                # Validate required fields
                required_fields = ["name", "mykad", "gender", "ethnicity", "p_mobile_no", "p_email", "postcode", "state", "address", "occupation"]
                missing_fields = [field for field in required_fields if not data.get(field)]
                if missing_fields:
                    return jsonify({"status": "failed", "message": f"Missing fields: {', '.join(missing_fields)}"}), 400

                # Validate medical history
                medical_history_list = []
                for history in medical_history:
                    condition = history.get("condition")
                    medicine = history.get("medicine")

                    if not all([condition, medicine]):
                        return jsonify({"status": "failed", "message": "Each medical history entry must include 'condition' and 'medicine'"}), 400

                    medical_history_list.append(MedicalHistory(condition=condition, medicine=medicine))

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
                    occupation=occupation
                )

                # Add medical history entries to the patient
                patient.medical_histories.extend(medical_history_list)

                db.session.add(patient)
                db.session.commit()

                return jsonify({"status": "success", "message": "Patient registered successfully"}), 201

            except Exception as e:
                db.session.rollback()  # Rollback transaction in case of an error
                return jsonify({"status": "failed", "message": str(e)}), 500

    # Export the information of ALL patients or 1 specific Patient
    @app.route("/export-patients", methods=["GET", "POST"])
    def export_patients():
        try:
            # Parse the patient ID from the FormData
            patient_id = request.form.get('patient_id')

            if patient_id:
                # Retrieve the specific patient by ID
                patient = Patient.query.get(patient_id)

                if not patient:
                    return jsonify({"status": "failed", "message": "Patient not found"}), 404

                # Retrieve the patient's medical history
                medical_history = [
                    {
                        "id": history.id,
                        "condition": history.condition,
                        "medicine": history.medicine
                    } for history in patient.medical_histories
                ]

                # Return the specific patient's information
                patient_data = {
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
                    "medical_history": medical_history,
                }
                return Response(
                    json.dumps(patient_data, ensure_ascii=False, indent=4),
                    mimetype="application/json",
                )

            else:
                # Retrieve all patients from the database
                patients = Patient.query.all()

                # Create a list of patient dictionaries
                patient_list = []
                for patient in patients:
                    # Retrieve each patient's medical history
                    medical_history = [
                        {
                            "id": history.id,
                            "condition": history.condition,
                            "medicine": history.medicine
                        } for history in patient.medical_histories
                    ]

                    # Append the patient dictionary
                    patient_list.append(
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
                            "medical_history": medical_history,
                        }
                    )

                # Create a JSON response
                response = Response(
                    json.dumps(patient_list, ensure_ascii=False, indent=4),
                    mimetype="application/json",
                )
                return response

        except Exception as e:
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

    # Submit Treatment Record for a Patient
    @app.route('/submit-treatment', methods=['POST'])
    def submit_treatment():
        try:
            
            if not session.get('user_id') or "therapists" not in session.get('role', []):
                return jsonify({"status": "failed", "message": "Unauthorized access"}), 403
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



    # Export ALL of a specific patient's record
    @app.route("/export-patient-record", methods=["POST"])
    def export_patient_records():
        try:

            if not session.get('user_id'):
                return jsonify({"status": "failed", "message": "Unauthorized access"}), 403

            # Get patient ID from form data
            patient_id = request.form.get("patient_id")

            if not patient_id:
                return jsonify({"status": "failed", "message": "Patient ID is required"}), 400

            # Query the patient records for the given patient ID
            patient_records = PatientRecord.query.filter_by(patient_id=patient_id).all()

            if not patient_records:
                return jsonify({"status": "failed", "message": "No records found for the given patient ID"}), 404

            # Prepare data
            records_data = []

            for record in patient_records:
                # Query acupuncture points related to the record
                acupoints = AcupuncturePoint.query.filter_by(record_id=record.record_id).all()

                # Group acupuncture points by body part
                remarks = {}
                for acupoint in acupoints:
                    body_part = acupoint.body_part
                    if body_part not in remarks:
                        remarks[body_part] = []
                    remarks[body_part].append({
                        "coordinate_x": acupoint.coordinate_x,
                        "coordinate_y": acupoint.coordinate_y,
                        "skin_reaction": acupoint.skin_reaction,
                        "blood_quantity": acupoint.blood_quantity,
                    })

                # Convert remarks dictionary into the required format
                remarks_list = [
                    {"body_part": part, "acupoint": points} for part, points in remarks.items()
                ]

                # Append record data
                records_data.append({
                    "id": record.record_id,
                    "patient_id": record.patient_id,
                    "therapist_id": record.therapist_id,
                    "created_data": record.date.strftime("%d/%m/%Y"),
                    "frequency": record.frequency,
                    "blood_pressure_before": record.blood_pressure_before,
                    "blood_pressure_after": record.blood_pressure_after,
                    "package": record.package,
                    "health_complications": record.health_complications,
                    "comments": record.comments,
                    "remarks": remarks_list,
                })

            return jsonify({"status": "success", "data": records_data}), 200

        except Exception as e:
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

    # Export a specific patient's specific record
    @app.route("/export-patient-record-visit", methods=["POST"])
    def export_patient_record_visit():
        try:

            if not session.get('user_id'):
                return jsonify({"status": "failed", "message": "Unauthorized access"}), 403

            # Get patient ID and frequency from form data
            patient_id = request.form.get("patient_id")
            record_id = request.form.get("record_id")

            if not patient_id or not record_id:
                return jsonify({"status": "failed", "message": "Patient ID and Record ID are required"}), 400

            # Query the patient record for the given patient ID and record id
            record = PatientRecord.query.filter_by(patient_id=patient_id, record_id=record_id).first()

            if not record:
                return jsonify({"status": "failed", "message": "No record found for the given patient ID and record ID"}), 404

            # Query acupuncture points related to the record
            acupoints = AcupuncturePoint.query.filter_by(record_id=record.record_id).all()

            # Group acupuncture points by body part
            remarks = {}
            for acupoint in acupoints:
                body_part = acupoint.body_part
                if body_part not in remarks:
                    remarks[body_part] = []
                remarks[body_part].append({
                    "coordinate_x": acupoint.coordinate_x,
                    "coordinate_y": acupoint.coordinate_y,
                    "skin_reaction": acupoint.skin_reaction,
                    "blood_quantity": acupoint.blood_quantity,
                })

            # Convert remarks dictionary into the required format
            remarks_list = [
                {"body_part": part, "acupoint": points} for part, points in remarks.items()
            ]

            # Prepare the data
            record_data = {
                "id": record.record_id,
                "patient_id": record.patient_id,
                "therapist_id": record.therapist_id,
                "created_data": record.date.strftime("%d/%m/%Y"),
                "frequency": record.frequency,
                "blood_pressure_before": record.blood_pressure_before,
                "blood_pressure_after": record.blood_pressure_after,
                "package": record.package,
                "health_complications": record.health_complications,
                "comments": record.comments,
                "remarks": remarks_list,
            }

            return jsonify({"status": "success", "data": record_data}), 200

        except Exception as e:
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

    # Exports ALL of a Specific Patient's Record but simplified to ID, frequency, Created Date and Package
    @app.route("/export-patient-simplify", methods=["POST"])
    def export_patient_simplify():
        try:

            if not session.get('user_id'):
                return jsonify({"status": "failed", "message": "Unauthorized access"}), 403

            # Get patient ID from form data
            patient_id = request.form.get("patient_id")

            if not patient_id:
                return jsonify({"status": "failed", "message": "Patient ID is required"}), 400

            # Query the patient records for the given patient ID
            patient_records = PatientRecord.query.filter_by(patient_id=patient_id).all()

            if not patient_records:
                return jsonify({"status": "failed", "message": "No records found for the given patient ID"}), 404

            # Prepare data
            records_data = []

            for record in patient_records:
                records_data.append({
                    "record_id": record.record_id,
                    "frequency": record.frequency,
                    "created_date": record.date.strftime("%Y-%m-%d"),
                    "Package": record.package,
                })

            return jsonify({"status": "success", "patient_id": patient_id, "records": records_data}), 200

        except Exception as e:
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

    # Delete Specific Record
    @app.route('/delete-record', methods=['POST'])
    def delete_record():
        try:
            # Check if the user is authorized
            # if not session.get('user_id'):
            #     return jsonify({"status": "failed", "message": "Unauthorized access"}), 403

            # Parse the record_id from FormData
            record_id = request.form.get('record_id')

            if not record_id:
                return jsonify({"status": "failed", "message": "Missing record_id"}), 400

            # Fetch the PatientRecord
            patient_record = PatientRecord.query.get(record_id)
            if not patient_record:
                return jsonify({"status": "failed", "message": "Record not found"}), 404

            # Delete associated AcupuncturePoint records
            AcupuncturePoint.query.filter_by(record_id=record_id).delete()

            # Delete the PatientRecord
            db.session.delete(patient_record)

            # Commit the changes
            db.session.commit()

            return jsonify({"status": "success", "message": "Record and associated points deleted successfully"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "failed", "message": str(e)}), 500

    # Delete Specific Patient
    @app.route('/delete-patient', methods=['POST'])
    def delete_patient():
        try:
            # Check if the user is authorized
            # if not session.get('user_id'):
            #     return jsonify({"status": "failed", "message": "Unauthorized access"}), 403

            # Parse the patient_id from FormData
            patient_id = request.form.get('patient_id')

            if not patient_id:
                return jsonify({"status": "failed", "message": "Missing patient_id"}), 400

            # Fetch the patient
            patient = Patient.query.get(patient_id)
            if not patient:
                return jsonify({"status": "failed", "message": "Patient not found"}), 404

            # Delete all associated patient records
            patient_records = PatientRecord.query.filter_by(patient_id=patient_id).all()
            for record in patient_records:
                # Delete associated acupuncture points for each record
                AcupuncturePoint.query.filter_by(record_id=record.record_id).delete()
                db.session.delete(record)

            # Delete the patient
            db.session.delete(patient)

            # Commit the changes
            db.session.commit()

            return jsonify({"status": "success", "message": "Patient and all associated records deleted successfully"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "failed", "message": str(e)}), 500

    # Update a specific patient's record with the matching ID
    @app.route("/update-patient", methods=["POST"])
    def update_patient():
        try:
            # Parse the JSON data from the request body
            data = request.get_json()
            if not data:
                return jsonify({"status": "failed", "message": "Invalid or missing JSON data"}), 400

            # Extract patient ID from the JSON payload
            patient_id = data.get("patient_id")
            if not patient_id:
                return jsonify({"status": "failed", "message": "Patient ID is required"}), 400

            # Retrieve the patient record by ID
            patient = Patient.query.get(patient_id)
            if not patient:
                return jsonify({"status": "failed", "message": "Patient not found"}), 404

            # Update patient details if provided
            patient.name = data.get("name", patient.name)
            patient.mykad = data.get("mykad", patient.mykad)
            patient.gender = data.get("gender", patient.gender)
            patient.ethnicity = data.get("ethnicity", patient.ethnicity)
            patient.p_mobile_no = data.get("p_mobile_no", patient.p_mobile_no)
            patient.p_email = data.get("p_email", patient.p_email)
            patient.postcode = data.get("postcode", patient.postcode)
            patient.state = data.get("state", patient.state)
            patient.address = data.get("address", patient.address)
            patient.occupation = data.get("occupation", patient.occupation)

            # Update medical history
            updated_medical_history = data.get("medical_history", [])
            if updated_medical_history:
                # Convert list of medical history dictionaries to a set of tuples for comparison
                updated_history_set = {(entry["condition"], entry["medicine"]) for entry in updated_medical_history}

                # Query the current medical history records for this patient
                current_history = MedicalHistory.query.filter_by(patient_id=patient_id).all()
                current_history_set = {(mh.condition, mh.medicine) for mh in current_history}

                # Determine new entries to add and existing entries to delete
                new_entries = updated_history_set - current_history_set
                to_delete = current_history_set - updated_history_set

                # Delete outdated medical history entries
                for mh in current_history:
                    if (mh.condition, mh.medicine) in to_delete:
                        db.session.delete(mh)

                # Add new medical history entries
                for condition, medicine in new_entries:
                    new_mh = MedicalHistory(
                        condition=condition,
                        medicine=medicine,
                        patient_id=patient_id
                    )
                    db.session.add(new_mh)

            # Commit all changes to the database
            db.session.commit()

            return jsonify({"status": "success", "message": "Patient and medical history updated successfully"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

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
            occupation="Engineer"
        )

        patient2 = Patient(
            name="Jane Doe",
            mykad="123456789021",
            gender="Female",
            ethnicity="Thiren",
            p_mobile_no="1234567891",
            p_email="janedoe@example.com",
            postcode="54321",
            state="Johor",
            address="456 Chocolate Street",
            occupation="Unknown"
        )

        history1 = MedicalHistory(
            patient_id="1",
            condition="Insanity",
            medicine="Cold Beer"
        )

        history2 = MedicalHistory(
            patient_id="1",
            condition="Paper Boats",
            medicine="Play Transistor"
        )

        record1 = PatientRecord(
            date=datetime.now(),
            frequency="1",
            blood_pressure_before="120/80",
            blood_pressure_after="118/78",
            package="Standard",
            health_complications="Mild headache",
            comments="Patient responded well",
            patient_id=1,  # Assuming this matches the patient primary key
            therapist_id=1  # Assuming this matches the user primary key
        )

        record2 = PatientRecord(
            date=datetime.now(),
            frequency="2",
            blood_pressure_before="120/80",
            blood_pressure_after="118/78",
            package="Special",
            health_complications="Evil",
            comments="Patient responded well enough",
            patient_id=1,  # Assuming this matches the patient primary key
            therapist_id=1  # Assuming this matches the user primary key
        )
        point1 = AcupuncturePoint(
            body_part="Front",
            coordinate_x=10.54,
            coordinate_y=24.44,
            skin_reaction=2,
            blood_quantity=5,
            record_id=1  # Assuming this matches the patient record primary key
        )

        point2 = AcupuncturePoint(
            body_part="Back",
            coordinate_x=10.12,
            coordinate_y=29.31,
            skin_reaction=2,
            blood_quantity=5,
            record_id=1  # Assuming this matches the patient record primary key
        )

        point3 = AcupuncturePoint(
            body_part="Front",
            coordinate_x=101.24,
            coordinate_y=205.50,
            skin_reaction=2,
            blood_quantity=5,
            record_id=2  # Assuming this matches the patient record primary key
        )
        db.session.add_all([user1, user2, user3, patient1, patient2])
        db.session.commit()

        db.session.add_all([record1, record2, history1, history2])
        db.session.commit()

        db.session.add_all([point1, point2, point3])
        db.session.commit()
        return redirect(url_for("index"))

