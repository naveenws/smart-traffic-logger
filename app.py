import os
import io
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import qrcode
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Support both local SQLite and Cloud PostgreSQL (Supabase)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///traffic.db').strip()

# Auto-fix if user forgot the protocol prefix
if "://" not in db_url:
    db_url = "postgresql+pg8000://" + db_url

if db_url.startswith("postgres://") or db_url.startswith("postgresql://"):
    # Force SQLAlchemy to use pure-python pg8000 to bypass Python 3.14 C-API bugs on Render
    db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    if "supabase" in db_url and "sslmode" not in db_url:
        db_url += "&sslmode=require" if "?" in db_url else "?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='officer')

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challan_id = db.Column(db.String(50), unique=True, nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    violation_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    fine_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Unpaid')
    qr_code_path = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/qr_code/<challan_id>.png')
def serve_qr_code(challan_id):
    # Generates a QR code linking to the specific challan status dynamically in-memory
    try:
        base_url = request.host_url.rstrip('/')
    except RuntimeError:
        base_url = "http://127.0.0.1:5000"
        
    url = f"{base_url}/challan/{challan_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number').upper()
        violation_type = request.form.get('violation_type')
        location = request.form.get('location')
        fine_amount = float(request.form.get('fine_amount'))
        
        challan_id = str(uuid.uuid4())[:8].upper() # Generate 8 char ID
        
        new_violation = Violation(
            challan_id=challan_id,
            vehicle_number=vehicle_number,
            violation_type=violation_type,
            location=location,
            fine_amount=fine_amount
        )
        
        # Save to DB
        db.session.add(new_violation)
        db.session.commit()
        
        flash('Violation recorded successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    violations = Violation.query.order_by(Violation.date_issued.desc()).all()
    return render_template('admin_dashboard.html', violations=violations)

@app.route('/add_officer', methods=['POST'])
@login_required
def add_officer():
    username = request.form.get('new_username')
    password = request.form.get('new_password')
    
    if User.query.filter_by(username=username).first():
        flash(f"Error: Username '{username}' already exists!", 'danger')
    else:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_admin = User(username=username, password=hashed_password, role='officer')
        db.session.add(new_admin)
        db.session.commit()
        flash(f"Success! New officer '{username}' added securely.", 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/update_status/<int:violation_id>', methods=['POST'])
@login_required
def update_status(violation_id):
    violation = Violation.query.get_or_404(violation_id)
    if violation.status == 'Unpaid':
        violation.status = 'Paid'
        db.session.commit()
        flash(f'Status for {violation.vehicle_number} updated to Paid.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/challan/<challan_id>')
def view_challan(challan_id):
    violation = Violation.query.filter_by(challan_id=challan_id).first_or_404()
    return render_template('challan.html', violation=violation)

@app.route('/search', methods=['GET'])
def search_vehicle():
    vehicle_number = request.args.get('vehicle_number')
    if vehicle_number:
        violations = Violation.query.filter_by(vehicle_number=vehicle_number.upper()).all()
        return render_template('search_results.html', violations=violations, vehicle_number=vehicle_number.upper())
    return redirect(url_for('index'))

# Initialize database automatically when the app starts
with app.app_context():
    try:
        db.create_all()
        # Create an admin user if none exists
        if not User.query.filter_by(username='admin').first():
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin = User(username='admin', password=hashed_password, role='admin')
            db.session.add(admin)
            db.session.commit()
    except Exception as e:
        print(f"Warning: Database initialization failed. Check your DATABASE_URL. Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
