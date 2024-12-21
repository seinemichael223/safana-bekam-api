from flask import render_template, request, redirect, url_for, jsonify, Response
from flask_login import login_user, logout_user, current_user, login_required
import json, os

from models import User, Patient


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
    @login_required
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
            # Parse JSON data from the request
            data = request.get_json()
            if not data:
                return jsonify({"status": "failed", "message": "No JSON payload received"}), 400

            # Extract data
            name = data.get("name")
            mykad = data.get("mykad")
            gender = data.get("gender")
            ethnicity = data.get("ethnicity")
            p_mobile_no = data.get("p_mobile_no")
            p_email = data.get("p_email")
            postcode = data.get("postcode")
            state = data.get("state")
            address = data.get("address")

            # Validate required fields
            required_fields = ["name", "mykad", "gender", "ethnicity", "p_mobile_no", "p_email", "postcode", "state", "address"]
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return jsonify({"status": "failed", "message": f"Missing fields: {', '.join(missing_fields)}"}), 400

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
            )

            db.session.add(patient)
            db.session.commit()

            return jsonify({"status": "success", "message": "Patient registered successfully"}), 201

        except Exception as e:
            return jsonify({"status": "failed", "message": str(e)}), 500


