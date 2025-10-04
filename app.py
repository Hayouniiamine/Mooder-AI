from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import logging
import requests  # For Spotify API requests
from spotify_api import get_playlist_for_mood, fetch_spotify_playlist_info  # Import functions from spotify_api.py

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')

# Database Configuration (PostgreSQL)
database_url = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/mooderdb")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret Key and Session Configuration
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecretkey")
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"

# Initialize Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
migrate = Migrate(app, db)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for('signup'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another one.', 'error')
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already in use. Please log in.', 'error')
            return redirect(url_for('login'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user, remember=True)
        session['user_id'] = new_user.id
        flash('Signup successful! Redirecting...', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    mood = session.get('mood', None)
    return render_template('dashboard.html', mood=mood)
@app.route('/detect_mood', methods=['POST'])
@login_required
def detect_mood_route():
    try:
        # Get the mood from the frontend (face-recognition.js)
        mood = request.json.get('mood')  # The frontend sends the detected mood

        if not mood:
            return jsonify({'error': 'No mood detected. Please try again.'}), 400

        logger.info(f'Mood detected: {mood}')
        
        # Store the detected mood in session
        session['mood'] = mood

        # Return response to frontend with a message and redirect URL
        response = jsonify({
            'mood': mood,
            'message': f"You look {mood}! 🎉",
            'redirect': url_for('player', mood=mood)
        })
        return response, 200
    except Exception as e:
        logger.error(f'Error detecting mood: {str(e)}')
        return jsonify({'error': 'An error occurred while detecting mood. Please try again later.'}), 500

@app.route('/player')
@login_required
def player():
    mood = request.args.get('mood', 'neutral')  # Default to 'neutral' if no mood is passed
    playlist_url = get_playlist_for_mood(mood)
    playlist_id = playlist_url.split('/')[-1]  # Extract ID from URL
    playlist_info = fetch_spotify_playlist_info(playlist_id)  # Fetch additional playlist info
    return render_template('player.html', mood=mood, playlist_id=playlist_id, playlist_info=playlist_info)

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/get_playlist_url/<mood>', methods=['GET'])
@login_required
def get_playlist_url(mood):
    try:
        playlist_url = get_playlist_for_mood(mood)
        return jsonify({'playlist_url': playlist_url}), 200
    except Exception as e:
        logger.error(f'Error fetching playlist for mood {mood}: {str(e)}')
        return jsonify({'error': 'Error fetching playlist URL'}), 500

@app.route('/get_playlist_info/<playlist_id>', methods=['GET'])
@login_required
def get_playlist_info(playlist_id):
    try:
        playlist_info = fetch_spotify_playlist_info(playlist_id)
        return jsonify(playlist_info), 200
    except Exception as e:
        logger.error(f'Error fetching playlist info for {playlist_id}: {str(e)}')
        return jsonify({'error': 'Error fetching playlist information'}), 500

@app.route('/models/<path:filename>')
def serve_model(filename):
    model_dir = os.path.join(app.root_path, 'static/js/face-api.js-master/weights')
    return send_from_directory(model_dir, filename)

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            logger.error(f"Database error: {e}")
    app.run(debug=True)
