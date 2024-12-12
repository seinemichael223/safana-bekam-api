from flask import render_template, request, redirect, url_for, jsonify, Response
from flask_login import login_user, logout_user, current_user, login_required
import json

from models import User


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

            hashed_password = bcrypt.generate_password_hash(password)

            user = User(email=email, username=username, password=hashed_password)

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
            return jsonify({"status": "failed",}), 404

        # Check password
        if bcrypt.check_password_hash(user.password, password):
            # Log the user in
            login_user(user)
            # Return a success JSON response
            return jsonify({"status": "success"}), 200
        else:
            # Return error for invalid password
            return jsonify({"status": "failed"}), 401

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
                'email': user.email,
                'username': user.username,
                'password': user.password
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


