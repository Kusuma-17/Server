import os
from datetime import datetime, timedelta
from flask import Flask, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# Load environment variables
load_dotenv()

# Database configuration using provided PostgreSQL connection string
DATABASE_URL = "postgresql://kusuma:E3Gstn7&CUqMqASi%AX@167.235.195.77:5432/kusuma"

# Set up configuration for Flask app
class Config:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')  # JWT secret key
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # Token expires in 1 hour

# Initialize Flask app and configurations
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)  # Initialize JWTManager

# Define User model
class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed password

# Define Log model for the logs table
class Log(db.Model):
    __tablename__ = 'logs'
    __table_args__ = {"schema": "public"}
    id = db.Column(db.Integer, primary_key=True)
    action_taken = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Helper function to add a log entry
def add_log(action_taken):
    log_entry = Log(action_taken=action_taken, timestamp=datetime.now())
    db.session.add(log_entry)
    db.session.commit()

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
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required'}), 400

    # Hash the password (you should use a proper hashing method in a production app)
    # Example using plain text password (for simplicity, use hashed passwords in real apps)
    user = User(name=name, email=email, password=password)
    db.session.add(user)
    db.session.commit()

    # Log the registration action
    add_log("registration")

    return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 201

# POST /login - Login route to create JWT token
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:  # In production, check hashed password
        return jsonify({'error': 'Invalid credentials'}), 401

    # Create JWT token
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200

# GET /users/<id> - Retrieve a user by ID (JWT protected)
@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()  # Ensure that the user is logged in
def get_user(user_id):
    current_user_id = get_jwt_identity()  # Get the user ID from the JWT token

    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403  # Unauthorized

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 200

# PUT /users/<id> - Update a user's details by ID (JWT protected)
@user_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def edit_user(user_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403

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

# DELETE /users/<id> - Delete a user by ID (JWT protected)
@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403

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
