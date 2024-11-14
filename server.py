import os
from datetime import datetime
from flask import Flask, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration using provided PostgreSQL connection string
DATABASE_URL = "postgresql://kusuma:E3Gstn7&CUqMqASi%AX@167.235.195.77:5432/kusuma"

# Set up configuration for Flask app
class Config:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL  # Use provided PostgreSQL connection string
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Initialize Flask app and configurations
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define User model
class User(db.Model):
    _tablename_ = 'users'
    _table_args_ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

# Define Log model for the logs table
class Log(db.Model):
    _tablename_ = 'logs'
    _table_args_ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    action_taken = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Attempt to create database tables if they don’t exist
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating tables: {e}")

# Blueprint for user routes
user_bp = Blueprint('users', __name__)

# Helper function to add a log entry
def add_log(action_taken):
    log_entry = Log(action_taken=action_taken, timestamp=datetime.now())
    db.session.add(log_entry)
    db.session.commit()

# POST /users - Create a new user
@user_bp.route('/', methods=['POST'])
def create_user():
    """
    Postman:
    - Method: POST
    - URL: http://<server-url>/users/
    - Body: JSON
        {
            "name": "John Doe",
            "email": "johndoe@example.com"
        }
    - Description: Creates a new user with the provided name and email.
    """
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400

    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    
    # Log the registration action
    add_log("registration")

    return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 201

# GET /users/<id> - Retrieve a user by ID
@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Postman:
    - Method: GET
    - URL: http://<server-url>/users/<user_id>
    - Description: Retrieves the user details based on the provided user ID.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 200

# PUT /users/<id> - Update a user's details by ID
@user_bp.route('/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    """
    Postman:
    - Method: PUT
    - URL: http://<server-url>/users/<user_id>
    - Body: JSON
        {
            "name": "Jane Doe",
            "email": "janedoe@example.com"
        }
    - Description: Updates the user's name and/or email.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if name:
        user.name = name
    if email:
        user.email = email

    db.session.commit()
    
    # Log the edit action
    add_log("edit_user")

    return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 200

# DELETE /users/<id> - Delete a user by ID
@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Postman:
    - Method: DELETE
    - URL: http://<server-url>/users/<user_id>
    - Description: Deletes the user with the specified user ID.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    
    # Log the delete action
    add_log("delete_user")

    return '', 204

# Register blueprint
app.register_blueprint(user_bp, url_prefix='/users')

if __name__ == "_main_":
    app.run(port=5000)