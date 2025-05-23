from flask import render_template, request, redirect, url_for, jsonify, Response, session
from flask_login import login_user, logout_user, current_user, login_required
import json, os
from datetime import datetime, timedelta
from sqlalchemy import extract

from models import User, Patient, PatientRecord, AcupuncturePoint, MedicalHistory, Notifications
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
                    "therapists": ["therapists"],
                    "both": ["admin", "therapists"],
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

    # Exports ALL Users
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
                created_date = data.get("created_date")  # Optional field
                medical_history = data.get("medical_history", [])  # Default to an empty list if not provided

                # Validate required fields
                required_fields = ["name", "mykad", "gender", "ethnicity", "p_mobile_no", "p_email", "postcode", "state", "address", "occupation"]
                missing_fields = [field for field in required_fields if not data.get(field)]
                if missing_fields:
                    return jsonify({"status": "failed", "message": f"Missing fields: {', '.join(missing_fields)}"}), 400

                # Generate a created_date if not provided
                if not created_date:
                    created_date = datetime.now().strftime('%Y-%m-%d')

                # Validate medical history
                medical_history_list = []
                for history in medical_history:
                    condition = history.get("condition")
                    medicine = history.get("medicine", "")  # Default to an empty string if not provided

                    if not condition:  # Condition is mandatory
                        return jsonify({"status": "failed", "message": "Each medical history entry must include 'condition'"}), 400

                    medical_history_list.append(MedicalHistory(condition=condition, medicine=medicine or ""))

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
                    date=datetime.strptime(created_date, '%Y-%m-%d')
                )

                # Add medical history entries to the patient
                patient.medical_histories.extend(medical_history_list)

                db.session.add(patient)
                db.session.flush()  # Flush to generate patient ID before using it in notification

                # Insert a notification for the new patient
                notification = Notifications(
                    date=datetime.strptime(created_date, '%Y-%m-%d'),
                    notif_type="tambah pelanggan",
                    message=f"New Patient, {name} added on {created_date}",
                )
                db.session.add(notification)

                # Commit the transaction
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
                    "created_date": patient.date.strftime("%d/%m/%Y"),
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
                            "created_date": patient.date.strftime("%d/%m/%Y"),
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
            # if not session.get('user_id') or "therapists" not in session.get('role', []):
            #     return jsonify({"status": "failed", "message": "Unauthorized access"}), 403

            # Parse data from the request
            data = request.get_json()

            # Extract treatment details
            patient_id = data.get('patient_id')
            therapist_id = data.get('therapist_id')
            created_date = data.get('created_date')  # Optional field
            frequency = data.get('frequency')
            blood_pressure_before = data.get('blood_pressure_before')
            blood_pressure_after = data.get('blood_pressure_after')
            package = data.get('package')
            health_complications = data.get('health_complications')
            comments = data.get('comments')
            acupuncture_points = data.get('acupuncture_point')

            # Validate required fields
            required_fields = ['patient_id', 'therapist_id', 'frequency', 'blood_pressure_before', 'blood_pressure_after', 'package']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400

            # Generate created_date if not provided
            if not created_date:
                created_date = datetime.now().strftime('%Y-%m-%d')

            # Retrieve patient details for notification
            patient = Patient.query.get(patient_id)
            if not patient:
                return jsonify({'error': 'Invalid patient ID'}), 404

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
                    # Unpack point details
                    body_part = point.get('body_part')
                    coordinate_x = point.get('coordinate_x')
                    coordinate_y = point.get('coordinate_y')
                    skin_reaction = point.get('skin_reaction')
                    blood_quantity = point.get('blood_quantity')

                    # Validate all required fields for acupuncture points
                    if not all([body_part, coordinate_x, coordinate_y, skin_reaction, blood_quantity]):
                        return jsonify({'error': 'Each acupuncture point must include body_part, coordinate_x, coordinate_y, skin_reaction, and blood_quantity'}), 400

                    # Add acupuncture point record
                    acupuncture_point = AcupuncturePoint(
                        body_part=body_part,
                        coordinate_x=coordinate_x,
                        coordinate_y=coordinate_y,
                        skin_reaction=skin_reaction,
                        blood_quantity=blood_quantity,
                        record_id=patient_record.record_id
                    )
                    db.session.add(acupuncture_point)

            # Create a notification for the treatment submission
            notification_message = f"New Treatment added for {patient.name} on {created_date}"
            notification = Notifications(
                date=datetime.strptime(created_date, '%Y-%m-%d'),
                notif_type="rekod rawatan baharu",
                message=notification_message
            )
            db.session.add(notification)

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
                    "created_date": record.date.strftime("%d/%m/%Y"),
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
                "created_date": record.date.strftime("%d/%m/%Y"),
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

            # Automatically update the date to today's date
            patient.date = datetime.now()

            # Update medical history
            updated_medical_history = data.get("medical_history", None)  # Explicitly handle None

            if updated_medical_history is None:
                # If no medical history is provided, delete all existing records
                MedicalHistory.query.filter_by(patient_id=patient_id).delete()
            else:
                # Convert the updated medical history to a dictionary for easy lookup
                updated_history_dict = {entry["condition"]: entry["medicine"] for entry in updated_medical_history}

                # Query the current medical history records for this patient
                current_history = MedicalHistory.query.filter_by(patient_id=patient_id).all()

                # Track conditions to keep
                conditions_to_keep = set(updated_history_dict.keys())

                # Update existing records or delete outdated ones
                for mh in current_history:
                    if mh.condition in updated_history_dict:
                        # Update the medicine if the condition exists but the medicine is different
                        if mh.medicine != updated_history_dict[mh.condition]:
                            mh.medicine = updated_history_dict[mh.condition]
                    else:
                        # Delete medical history entries not in the updated list
                        db.session.delete(mh)

                # Add new medical history entries
                existing_conditions = {mh.condition for mh in current_history}
                for condition, medicine in updated_history_dict.items():
                    if condition not in existing_conditions:
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
            occupation="Engineer",
            date=datetime.now()
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
            occupation="Unknown",
            date=datetime.now()
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
            coordinate_x="10.54",
            coordinate_y="24.44",
            skin_reaction=2,
            blood_quantity=5,
            record_id=1  # Assuming this matches the patient record primary key
        )

        point2 = AcupuncturePoint(
            body_part="Back",
            coordinate_x="10.12",
            coordinate_y="29.31",
            skin_reaction=2,
            blood_quantity=5,
            record_id=1  # Assuming this matches the patient record primary key
        )

        point3 = AcupuncturePoint(
            body_part="Front",
            coordinate_x="101.24",
            coordinate_y="205.50",
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

    @app.route('/update-treatment-record', methods=['POST'])
    def update_treatment_record():
        try:
            # Parse data from the request
            data = request.get_json()
            if not data:
                return jsonify({"status": "failed", "message": "Invalid or missing JSON data"}), 400

            # Extract record ID
            record_id = data.get('record_id')
            if not record_id:
                return jsonify({"status": "failed", "message": "Record ID is required"}), 400

            # Retrieve the record by ID
            patient_record = PatientRecord.query.get(record_id)
            if not patient_record:
                return jsonify({"status": "failed", "message": "Patient record not found"}), 404

            # Update patient record fields if provided
            patient_record.date = datetime.strptime(data.get('created_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
            patient_record.frequency = data.get('frequency', patient_record.frequency)
            patient_record.blood_pressure_before = data.get('blood_pressure_before', patient_record.blood_pressure_before)
            patient_record.blood_pressure_after = data.get('blood_pressure_after', patient_record.blood_pressure_after)
            patient_record.package = data.get('package', patient_record.package)
            patient_record.health_complications = data.get('health_complications', patient_record.health_complications)
            patient_record.comments = data.get('comments', patient_record.comments)

            # Handle acupuncture points
            updated_acupuncture_points = data.get('acupuncture_point', [])
            if updated_acupuncture_points:
                # Convert the updated points to a set of tuples for easy comparison
                updated_points_set = {
                    (point['body_part'], point['coordinate_x'], point['coordinate_y'], point['skin_reaction'], point['blood_quantity'])
                    for point in updated_acupuncture_points
                }

                # Query existing acupuncture points
                current_points = AcupuncturePoint.query.filter_by(record_id=record_id).all()
                current_points_set = {
                    (point.body_part, point.coordinate_x, point.coordinate_y, point.skin_reaction, point.blood_quantity)
                    for point in current_points
                }

                # Determine points to add, update, or delete
                points_to_add = updated_points_set - current_points_set
                points_to_keep = updated_points_set & current_points_set
                points_to_delete = current_points_set - updated_points_set

                # Delete outdated points
                for point in current_points:
                    if (point.body_part, point.coordinate_x, point.coordinate_y, point.skin_reaction, point.blood_quantity) in points_to_delete:
                        db.session.delete(point)

                # Add new points
                for point_data in points_to_add:
                    body_part, coordinate_x, coordinate_y, skin_reaction, blood_quantity = point_data
                    new_point = AcupuncturePoint(
                        body_part=body_part,
                        coordinate_x=coordinate_x,
                        coordinate_y=coordinate_y,
                        skin_reaction=skin_reaction,
                        blood_quantity=blood_quantity,
                        record_id=record_id
                    )
                    db.session.add(new_point)

            # Commit all changes
            db.session.commit()

            return jsonify({"status": "success", "message": "Treatment record updated successfully"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

    @app.route("/update-user", methods=["POST"])
    def update_user():
        try:
            # Retrieve user ID and updated details from the form
            user_id = request.form.get("user_id")
            email = request.form.get("email")
            username = request.form.get("username")
            mobile_no = request.form.get("mobile_no")
            address = request.form.get("address")
            roles = request.form.getlist("role")

            # Validate required fields
            if not user_id:
                return jsonify({"status": "failed", "message": "User ID is required"}), 400

            # Find the user by ID
            user = User.query.get(user_id)
            if not user:
                return jsonify({"status": "failed", "message": "User not found"}), 404

            # Update user particulars if provided
            if email:
                user.email = email
            if username:
                user.username = username
            if mobile_no:
                user.mobile_no = mobile_no
            if address:
                user.address = address

            # Update roles if provided
            if roles:
                if len(roles) == 2:
                    user.role = "both"
                elif "admin" in roles:
                    user.role = "admin"
                else:
                    user.role = "therapists"

            # Commit changes to the database
            db.session.commit()

            return jsonify({"status": "success", "message": "User updated successfully"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "failed", "message": f"An error occurred: {str(e)}"}), 500

    @app.route('/check-patients-monthly', methods=['GET'])
    def check_patient_monthly():
        try:
            # Calculate the date 30 days ago
            thirty_days_ago = datetime.now() - timedelta(days=30)

            # Query the database for patients registered in the past 30 days
            recent_patients_count = Patient.query.filter(Patient.date >= thirty_days_ago).count()

            # Return the count as JSON response
            return jsonify({
                "status": "success",
                "count": recent_patients_count
            }), 200

        except Exception as e:
            # Handle any errors
            return jsonify({
                "status": "failed",
                "message": f"An error occurred: {str(e)}"
            }), 500

    @app.route('/check-patients-daily', methods=['GET'])
    def check_patients_daily():
        try:
            # Calculate the date 24 hours ago
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

            # Query the database for patients registered in the past 24 hours
            recent_count = Patient.query.filter(Patient.date >= twenty_four_hours_ago).count()

            # Return the count as JSON response
            return jsonify({
                "status": "success",
                "count": recent_count
            }), 200

        except Exception as e:
            # Handle any errors
            return jsonify({
                "status": "failed",
                "message": f"An error occurred: {str(e)}"
            }), 500

    @app.route('/total-patients', methods=['GET'])
    def total_patients():
        try:
            # Query the total number of patients in the database
            total_count = Patient.query.count()

            # Return the count as JSON response
            return jsonify({
                "status": "success",
                "count": total_count
            }), 200

        except Exception as e:
            # Handle any errors
            return jsonify({
                "status": "failed",
                "message": f"An error occurred: {str(e)}"
            }), 500

    @app.route('/treatment-records-daily', methods=['GET'])
    def treatment_records_daily():
        try:
            # Calculate the date 24 hours ago
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

            # Query the database for patient records created in the past 24 hours
            recent_records_count = PatientRecord.query.filter(PatientRecord.date >= twenty_four_hours_ago).count()

            # Return the count as JSON response
            return jsonify({
                "status": "success",
                "count": recent_records_count
            }), 200

        except Exception as e:
            # Handle any errors
            return jsonify({
                "status": "failed",
                "message": f"An error occurred: {str(e)}"
            }), 500

    @app.route('/notifications', methods=['GET'])
    def get_recent_notifications():
        try:
            # Calculate the cutoff timestamp (48 hours ago)
            cutoff_time = datetime.utcnow() - timedelta(hours=48)

            # Query notifications created within the last 48 hours
            recent_notifications = Notifications.query.filter(Notifications.date >= cutoff_time).order_by(Notifications.date.desc()).all()

            # Serialize notifications
            result = [
                {
                    "notification_id": n.notif_id,
                    "notification_type": n.notif_type,
                    "message": n.message,
                    "date_created": n.date.isoformat()
                }
                for n in recent_notifications
            ]

            return jsonify({"status": "success", "notifications": result}), 200

        except Exception as e:
            return jsonify({"status": "failed", "message": str(e)}), 500

    @app.route('/check-patients-monthly-sorted', methods=['GET'])
    def check_patients_monthly_sorted():
        try:
            # Extract the year from the query parameters
            year = request.args.get('year', type=int)
            if not year:
                return jsonify({"error": "Year is required"}), 400

            # Query to count patients by month for the specified year
            patient_monthly_counts = db.session.query(
                extract('month', Patient.date).label('month'),
                db.func.count(Patient.pid).label('new_patients_registered')
            ).filter(
                extract('year', Patient.date) == year
            ).group_by(
                extract('month', Patient.date)
            ).order_by(
                extract('month', Patient.date)
            ).all()

            # Query to count treatment records by month for the specified year
            treatment_monthly_counts = db.session.query(
                extract('month', PatientRecord.date).label('month'),
                db.func.count(PatientRecord.record_id).label('new_treatment_records')
            ).filter(
                extract('year', PatientRecord.date) == year
            ).group_by(
                extract('month', PatientRecord.date)
            ).order_by(
                extract('month', PatientRecord.date)
            ).all()

            # Combine the results into a single response
            month_names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            result = {month: {"new_patients_registered": 0, "new_treatment_records": 0} for month in month_names}

            # Map patient data to the result
            for month, count in patient_monthly_counts:
                result[month_names[month - 1]]["new_patients_registered"] = count

            # Map treatment data to the result
            for month, count in treatment_monthly_counts:
                result[month_names[month - 1]]["new_treatment_records"] = count

            # Format the result for JSON response
            formatted_result = [{"month": month, **data} for month, data in result.items()]

            return jsonify({"status": "success", "data": formatted_result}), 200

        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
