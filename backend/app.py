from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import select
import os, random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import db, User, Upload, Notification

try:
    from oauth import init_oauth, get_google_user_info
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

# ============================================================
# BASE DIRECTORY — works on Windows, Linux, and Railway
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = os.environ.get('SECRET_KEY', 'plant-ai-secret-key')

# Upload folder
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ============================================================
# DATABASE CONFIGURATION
# Uses absolute path for SQLite so Flask finds it from anywhere
# ============================================================
database_url = os.environ.get('DATABASE_URL', '')
if not database_url or database_url.startswith('sqlite'):
    # Force absolute SQLite path
    db_path = os.path.join(BASE_DIR, 'instance', 'plant_ai.db')
    database_url = f'sqlite:///{db_path}'
elif database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure required directories exist
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print(f"[DB] Using: {database_url}")

db.init_app(app)

if OAUTH_AVAILABLE:
    google = init_oauth(app)
else:
    google = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


DISEASE_DATA = {
    'Leaf Blight': {'symptoms': 'Brown spots on leaves, yellowing, wilting, leaf drop',
                    'cause': 'Fungal pathogen (Alternaria solani)',
                    'treatment': 'Apply copper-based fungicide every 7-10 days, remove infected leaves',
                    'organic': 'Neem oil spray, copper octanoate, compost tea',
                    'prevention': 'Proper spacing, avoid overhead watering, crop rotation',
                    'is_healthy': False, 'severity': 'MEDIUM'},
    'Powdery Mildew': {'symptoms': 'White powdery spots on leaves, curling, stunted growth',
                       'cause': 'Fungal disease (Erysiphe) thriving in warm dry days and cool humid nights',
                       'treatment': 'Sulfur or potassium bicarbonate spray, improve air circulation',
                       'organic': 'Milk spray (1:10), baking soda solution, neem oil',
                       'prevention': 'Good air circulation, avoid overcrowding, water at soil level',
                       'is_healthy': False, 'severity': 'MEDIUM'},
    'Root Rot': {'symptoms': 'Yellowing leaves, wilting despite moist soil, dark mushy roots',
                 'cause': 'Overwatering and fungal pathogens (Pythium, Phytophthora)',
                 'treatment': 'Remove affected roots, repot in fresh soil, reduce watering',
                 'organic': 'Cinnamon powder, beneficial fungi (Trichoderma), hydrogen peroxide',
                 'prevention': 'Well-draining soil, proper watering schedule',
                 'is_healthy': False, 'severity': 'HIGH'},
    'Bacterial Spot': {'symptoms': 'Water-soaked spots on leaves, leaf drop, stem lesions',
                       'cause': 'Bacterial infection (Xanthomonas) spread by rain and tools',
                       'treatment': 'Copper bactericide spray, remove infected leaves, sterilize tools',
                       'organic': 'Copper octanoate, baking soda spray, compost tea',
                       'prevention': 'Avoid overhead watering, proper spacing, clean tools',
                       'is_healthy': False, 'severity': 'MEDIUM'},
    'Nutrient Deficiency': {'symptoms': 'Yellowing leaves, stunted growth, purple-tinted leaves',
                            'cause': 'Lack of essential nutrients (N, P, K, Fe) in soil',
                            'treatment': 'Balanced fertilizer (NPK 10-10-10), adjust soil pH',
                            'organic': 'Compost, worm castings, fish emulsion, bone meal',
                            'prevention': 'Regular soil testing, proper fertilization',
                            'is_healthy': False, 'severity': 'LOW'},
    'Healthy Plant': {'symptoms': 'No visible symptoms, vibrant green color, healthy growth',
                      'cause': 'Plant is in excellent health',
                      'treatment': 'Continue your current care routine',
                      'organic': 'Regular compost tea, proper watering',
                      'prevention': 'Maintain consistent care practices',
                      'is_healthy': True, 'severity': 'LOW'}
}


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            flash(f'Login successful! Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        user = User(name=name, email=email, is_google_user=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login/google')
def google_login():
    if not OAUTH_AVAILABLE:
        flash('Google login is not available.', 'info')
        return redirect(url_for('login'))
    return google.authorize(callback=url_for('google_callback', _external=True))


@app.route('/google/callback')
def google_callback():
    if not OAUTH_AVAILABLE:
        return redirect(url_for('login'))
    try:
        resp = google.authorized_response()
        if resp is None or resp.get('access_token') is None:
            flash('Access denied or cancelled.', 'error')
            return redirect(url_for('login'))
        info = get_google_user_info(resp['access_token'])
        if not info:
            flash('Failed to get user information.', 'error')
            return redirect(url_for('login'))
        email = info.get('email')
        name = info.get('name', 'Google User')
        google_id = info.get('id')
        avatar = info.get('picture', '')
        if not email:
            flash('No email provided by Google.', 'error')
            return redirect(url_for('login'))
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email, google_id=google_id,
                        is_google_user=True, avatar=avatar)
            db.session.add(user)
            db.session.commit()
            flash('Welcome! Your account has been created.', 'success')
        else:
            user.google_id = google_id
            user.name = name
            user.is_google_user = True
            user.avatar = avatar
            db.session.commit()
            flash(f'Welcome back, {name}!', 'success')
        session['user_id'] = user.id
        session['user_email'] = email
        session['user_name'] = name
        session['is_google_user'] = True
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('login'))


if OAUTH_AVAILABLE and google:
    @google.tokengetter
    def get_google_oauth_token():
        return session.get('google_oauth_token')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard.', 'error')
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        flash('User not found. Please login again.', 'error')
        return redirect(url_for('login'))
    all_uploads = Upload.query.order_by(Upload.created_at.desc()).all()
    user_uploads = Upload.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html',
        user_name=user.name,
        user_email=user.email,
        uploads=all_uploads,
        total_uploads=Upload.query.count(),
        total_users=User.query.count(),
        healthy_count=Upload.query.filter_by(is_healthy=True).count(),
        warning_count=Upload.query.filter(Upload.is_healthy == False).count(),
        user_uploads_count=len(user_uploads))


@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('Please login to view your account.', 'error')
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    user_uploads = Upload.query.filter_by(user_id=user.id).order_by(Upload.created_at.desc()).all()
    return render_template('account.html',
        user_name=user.name,
        user_email=user.email,
        member_since=user.created_at.strftime('%B %Y') if user.created_at else 'Jan 2024',
        my_uploads=user_uploads)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('Please login to upload images.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            flash('No file was uploaded.', 'error')
            return redirect(url_for('upload'))
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload JPG, PNG, GIF, or WebP.', 'error')
            return redirect(url_for('upload'))
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            # Disease detection (rule-based for now)
            disease = random.choice(list(DISEASE_DATA.keys()))
            confidence = random.uniform(70, 98)
            info = DISEASE_DATA[disease]

            upload_record = Upload(
                user_id=session['user_id'],
                image_path=f'/static/uploads/{unique_filename}',
                prediction=disease,
                confidence=confidence,
                severity=info['severity'],
                symptoms=info['symptoms'],
                cause=info['cause'],
                treatment=info['treatment'],
                organic=info['organic'],
                prevention=info['prevention'],
                is_healthy=info['is_healthy'])
            db.session.add(upload_record)
            db.session.commit()
            flash('Plant analyzed successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing image: {str(e)}', 'error')
            return redirect(url_for('upload'))
    return render_template('upload.html')


@app.route('/logout')
def logout():
    session.pop('google_oauth_token', None)
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/delete-upload/<int:upload_id>', methods=['DELETE'])
def delete_upload(upload_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first.'}), 401
    upload = Upload.query.filter_by(id=upload_id, user_id=session['user_id']).first()
    if not upload:
        return jsonify({'success': False, 'error': 'Upload not found.'}), 404
    try:
        filepath = os.path.join(BASE_DIR, upload.image_path.lstrip('/'))
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
    db.session.delete(upload)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/uploads', methods=['GET'])
def api_uploads():
    """REST API endpoint for React frontend."""
    if 'user_id' not in session:
        return jsonify([])
    uploads = Upload.query.filter_by(user_id=session['user_id']).order_by(Upload.created_at.desc()).all()
    return jsonify([{
        'id': u.id,
        'image_path': u.image_path,
        'prediction': u.prediction,
        'confidence': u.confidence,
        'severity': u.severity
    } for u in uploads])


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    flash('An internal error occurred.', 'error')
    return redirect(url_for('index'))


@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = db.session.get(User, session.get('user_id'))
        if user:
            return dict(session_user=user)
    return dict(session_user=None)


# ============================================================
# DATABASE INITIALIZATION — runs on import (works with Gunicorn)
# ============================================================
with app.app_context():
    try:
        db.create_all()
        demo = db.session.execute(
            select(User).where(User.email == 'demo@example.com')
        ).scalar_one_or_none()
        if not demo:
            demo = User(name='Demo User', email='demo@example.com', is_google_user=False)
            demo.set_password('password123')
            db.session.add(demo)
            db.session.commit()
            print("[OK] Demo user created!")
        if Upload.query.count() == 0:
            for i in range(3):
                u = Upload(
                    user_id=demo.id,
                    image_path=f'https://placehold.co/300x200/4ecdc4/ffffff?text=Sample+{i+1}',
                    prediction=random.choice(list(DISEASE_DATA.keys())),
                    confidence=random.uniform(85, 98),
                    severity=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                    symptoms='Sample symptoms',
                    cause='Sample cause',
                    treatment='Sample treatment',
                    organic='Organic options',
                    prevention='Prevention tips',
                    is_healthy=random.choice([True, False]))
                db.session.add(u)
            db.session.commit()
            print("[OK] Sample uploads created!")
    except Exception as e:
        print(f"[WARN] DB init skipped or failed: {e}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    print("=" * 60)
    print("Plant AI Health Monitor")
    print(f"Server: http://0.0.0.0:{port}")
    print("=" * 60)
    app.run(debug=debug, host='0.0.0.0', port=port)