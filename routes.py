from flask import render_template, request, redirect, url_for, jsonify, Response
from flask_login import login_user, logout_user, current_user, login_required
import json, os

from models import User

def get_domain_url():
    try:
        with open('secret.txt', 'r') as file:
            return file.read().strip()  # Remove any trailing newline or spaces
    except FileNotFoundError:
        raise Exception("secret.txt not found. Please add it to the root directory.")

domain_url = get_domain_url()

def register_routes(app, db, bcrypt):

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'GET':
            return render_template('signup.html')
        elif request.method == 'POST':
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            mobile_no = request.form.get('mobile_no')
            address = request.form.get('address')
            role = request.form.get('role')

            hashed_password = bcrypt.generate_password_hash(password)

            user = User(email=email,
                        username=username,
                        password=hashed_password,
                        mobile_no=mobile_no,
                        address=address,
                        role=role)

            db.session.add(user)
            db.session.commit()
            return redirect(url_for('index'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            # Query the user by username
            user = User.query.filter(User.username == username).first()

            if user is None:
                # Return error if user does not exist
                return jsonify({"status": "failed", "message": "User not found"}), 404

            # Check password
            if bcrypt.check_password_hash(user.password, password):
                # Log the user in
                login_user(user)

                # Return a JSON response with user details
                user_data = {
                    "status": "success",
                    "user": {
                        "id": user.uid,
                        "profile_picture": f"{domain_url}/static/profile_pictures/picture1.jpg",
                        "username": user.username,
                        "email": user.email,
                        "mobile_no": user.mobile_no,
                        "address": user.address,
                        "role": [user.role]
                    }
                }
                return jsonify(user_data), 200
            else:
                # Return error for invalid password
                return jsonify({"status": "failed", "message": "Invalid password"}), 401

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/secret')
    @login_required
    def secret():
        return 'My secret message'

    @app.route('/export-users', methods=['GET'])
    @login_required
    def export_users():
        try:
            # Query all users from the database
            users = User.query.all()
            user_list = [{
                'id': user.uid,
                'profile_picture': f"{domain_url}/static/profile_pictures/picture1.jpg",
                'username': user.username,
                'email': user.email,
                'password': user.password,
                'mobile_no': user.mobile_no,
                'address': user.address,
                'role': user.role
            } for user in users]

        # Convert the user list to JSON and return as a downloadable response
            response = Response(
                json.dumps(user_list, ensure_ascii=False, indent=4),
                mimetype='application/json'
            )
            return response

        except Exception as e:
        # Handle errors gracefully
            return f"An error occurred: {str(e)}", 500


