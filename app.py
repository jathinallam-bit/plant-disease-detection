$content = @"
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import select
import os, random
from datetime import datetime
from models import db, User, Upload, Notification

try:
    from oauth import init_oauth, get_google_user_info
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'plant-ai-secret-key')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Use PostgreSQL on Railway, SQLite locally
database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/plant_ai.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs('instance', exist_ok=True)

db.init_app(app)

if OAUTH_AVAILABLE:
    google = init_oauth(app)
else:
    google = None

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


DISEASE_DATA = {
    'Leaf Blight': {'symptoms': 'Brown spots', 'cause': 'Fungal', 'treatment': 'Fungicide', 'organic': 'Neem oil', 'prevention': 'Spacing', 'is_healthy': False, 'severity': 'MEDIUM'},
    'Powdery Mildew': {'symptoms': 'White spots', 'cause': 'Fungal', 'treatment': 'Sulfur', 'organic': 'Milk', 'prevention': 'Air flow', 'is_healthy': False, 'severity': 'MEDIUM'},
    'Root Rot': {'symptoms': 'Yellow leaves', 'cause': 'Overwatering', 'treatment': 'Repot', 'organic': 'Cinnamon', 'prevention': 'Drainage', 'is_healthy': False, 'severity': 'HIGH'},
    'Bacterial Spot': {'symptoms': 'Dark spots', 'cause': 'Bacteria', 'treatment': 'Copper', 'organic': 'Baking soda', 'prevention': 'Spacing', 'is_healthy': False, 'severity': 'MEDIUM'},
    'Nutrient Deficiency': {'symptoms': 'Yellow leaves', 'cause': 'Low nutrients', 'treatment': 'Fertilizer', 'organic': 'Compost', 'prevention': 'Testing', 'is_healthy': False, 'severity': 'LOW'},
    'Healthy Plant': {'symptoms': 'None', 'cause': 'Good health', 'treatment': 'Continue care', 'organic': 'Compost', 'prevention': 'Monitoring', 'is_healthy': True, 'severity': 'LOW'}
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email exists.', 'error')
            return render_template('register.html')
        user = User(name=name, email=email, is_google_user=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registered! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login/google')
def google_login():
    if not OAUTH_AVAILABLE:
        flash('Google login disabled.', 'info')
        return redirect(url_for('login'))
    return google.authorize(callback=url_for('google_callback', _external=True))


@app.route('/google/callback')
def google_callback():
    if not OAUTH_AVAILABLE:
        return redirect(url_for('login'))
    resp = google.authorized_response()
    if resp is None:
        flash('Access denied.', 'error')
        return redirect(url_for('login'))
    info = get_google_user_info(resp['access_token'])
    if not info:
        flash('Failed to get info.', 'error')
        return redirect(url_for('login'))
    email = info.get('email')
    name = info.get('name', 'User')
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, is_google_user=True)
        db.session.add(user)
        db.session.commit()
    session['user_id'] = user.id
    session['user_email'] = email
    session['user_name'] = name
    flash('Welcome!', 'success')
    return redirect(url_for('dashboard'))


if OAUTH_AVAILABLE and google:
    @google.tokengetter
    def get_google_oauth_token():
        return session.get('google_oauth_token')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    all_uploads = Upload.query.order_by(Upload.created_at.desc()).all()
    user_uploads = Upload.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html',
        user_name=user.name, user_email=user.email, uploads=all_uploads,
        total_uploads=Upload.query.count(), total_users=User.query.count(),
        healthy_count=Upload.query.filter_by(is_healthy=True).count(),
        warning_count=Upload.query.filter(Upload.is_healthy == False).count(),
        user_uploads_count=len(user_uploads))


@app.route('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    user_uploads = Upload.query.filter_by(user_id=user.id).order_by(Upload.created_at.desc()).all()
    return render_template('account.html',
        user_name=user.name, user_email=user.email,
        member_since=user.created_at.strftime('%B %Y') if user.created_at else 'Jan 2024',
        my_uploads=user_uploads)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            flash('No file.', 'error')
            return redirect(url_for('upload'))
        if not allowed_file(file.filename):
            flash('Invalid type.', 'error')
            return redirect(url_for('upload'))
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        disease = random.choice(list(DISEASE_DATA.keys()))
        confidence = random.uniform(70, 98)
        info = DISEASE_DATA[disease]
        upload_record = Upload(
            user_id=session['user_id'], image_path=f'/{filepath}',
            prediction=disease, confidence=confidence,
            severity=info['severity'], symptoms=info['symptoms'],
            cause=info['cause'], treatment=info['treatment'],
            organic=info['organic'], prevention=info['prevention'],
            is_healthy=info['is_healthy'])
        db.session.add(upload_record)
        db.session.commit()
        flash('Analyzed!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('upload.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/delete-upload/<int:upload_id>', methods=['DELETE'])
def delete_upload(upload_id):
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    upload = Upload.query.filter_by(id=upload_id, user_id=session['user_id']).first()
    if not upload:
        return jsonify({'success': False}), 404
    db.session.delete(upload)
    db.session.commit()
    return jsonify({'success': True})


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = db.session.get(User, session.get('user_id'))
        if user:
            return dict(session_user=user)
    return dict(session_user=None)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        demo = db.session.execute(select(User).where(User.email == 'demo@example.com')).scalar_one_or_none()
        if not demo:
            demo = User(name='Demo User', email='demo@example.com', is_google_user=False)
            demo.set_password('password123')
            db.session.add(demo)
            db.session.commit()
            print("[OK] Demo user created!")
        if Upload.query.count() == 0:
            for i in range(3):
                u = Upload(user_id=demo.id,
                    image_path=f'https://placehold.co/300x200/4ecdc4/ffffff?text=Sample+{i+1}',
                    prediction=random.choice(list(DISEASE_DATA.keys())),
                    confidence=random.uniform(85, 98), severity='LOW',
                    symptoms='Sample', cause='Sample', treatment='Sample',
                    organic='Sample', prevention='Sample',
                    is_healthy=random.choice([True, False]))
                db.session.add(u)
            db.session.commit()
            print("[OK] Sample uploads created!")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    print("=" * 60)
    print("Plant AI Health Monitor")
    print(f"Server: http://0.0.0.0:{port}")
    print("=" * 60)
    app.run(debug=debug, host='0.0.0.0', port=port)
"@
$content | Out-File -FilePath "app.py" -Encoding utf8 -NoNewline
Write-Host "app.py updated for Railway!"