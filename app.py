from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import os
import random
import string

# Initialize app, database, and login manager
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Using SQLite for simplicity
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong secret key
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    api_keys = db.relationship('ApiKey', backref='user', lazy=True)

# ApiKey model
class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(20), default='Active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Function to generate a random API key
def generate_api_key():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(32))  # Generates a 32-character key

# Route to serve the API Keys page
@app.route('/api-keys')
@login_required  # Ensure user is logged in to view API keys page
def api_keys():
    return render_template('api-keys.html')

# Route to generate API key
@app.route('/generate-key', methods=['POST'])
@login_required
def generate_key():
    user = current_user
    if len(user.api_keys) >= 5:
        return jsonify({'message': 'Maximum number of API keys reached.'}), 400

    new_key = generate_api_key()

    # Ensure the key is unique
    while ApiKey.query.filter_by(key=new_key).first():
        new_key = generate_api_key()

    # Create and save the new API key
    api_key = ApiKey(key=new_key, user_id=user.id)
    db.session.add(api_key)
    db.session.commit()

    return jsonify({'api_key': new_key})

# Route to get API keys data
@app.route('/api-keys-data', methods=['GET'])
@login_required
def get_api_keys():
    user = current_user
    api_keys = ApiKey.query.filter_by(user_id=user.id).all()
    api_keys_data = [
        {
            'key': api_key.key,
            'created_at': api_key.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': api_key.status
        }
        for api_key in api_keys
    ]
    return jsonify({'api_keys': api_keys_data})

# Route to regenerate API key
@app.route('/api-keys/<string:key>/regenerate', methods=['POST'])
@login_required
def regenerate_api_key(key):
    user = current_user
    api_key = ApiKey.query.filter_by(key=key, user_id=user.id).first()
    if not api_key:
        return jsonify({'message': 'API key not found.'}), 404

    # Generate a new unique key
    new_key = generate_api_key()
    while ApiKey.query.filter_by(key=new_key).first():
        new_key = generate_api_key()

    api_key.key = new_key
    api_key.created_at = db.func.now()
    api_key.status = 'Active'
    db.session.commit()

    return jsonify({'api_key': new_key})

# Route to delete API key
@app.route('/api-keys/<string:key>', methods=['DELETE'])
@login_required
def delete_api_key(key):
    user = current_user
    api_key = ApiKey.query.filter_by(key=key, user_id=user.id).first()
    if not api_key:
        return jsonify({'message': 'API key not found.'}), 404

    db.session.delete(api_key)
    db.session.commit()

    return jsonify({'message': 'API key deleted successfully.'}), 200

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login Successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api-docs')
def api_docs_view():
    return render_template('api_docs.html')

@app.route('/sumz-ai-2.5')
@login_required
def sumz_ai_2_5():
    return render_template('sumz_ai_2_5.html')

@app.route('/terms')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy_policy.html')


if __name__ == '__main__':
    with app.app_context():  # Use application context
        db.create_all()  # Create database tables
    app.run(debug=True, port=5000)  # Specify port 5000 explicitly
