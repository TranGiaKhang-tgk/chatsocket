import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'chat.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)
 

# Models

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# user loader (module-level)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please provide username and password', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('chat'))
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('login'))


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', username=current_user.username)

# SocketIO events


@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False  # refuse connection
    msg = f'{current_user.username} has connected.'
    emit('status', {'msg': msg}, broadcast=True)

 
@socketio.on('message')
def handle_message(msg):
    # msg should be a dict with 'msg' and optionally 'room'
    data = msg if isinstance(msg, dict) else {'msg': str(msg)}
    user = (
        current_user.username
        if current_user.is_authenticated
        else 'Anonymous'
    )
    data['user'] = user
    emit('message', data, broadcast=True)

 
@socketio.on('join')
def on_join(data):
    room = data.get('room')
    join_room(room)
    msg = f"{current_user.username} has entered the room {room}."
    emit('status', {'msg': msg}, room=room)

 
@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    leave_room(room)
    msg = f"{current_user.username} has left the room {room}."
    emit('status', {'msg': msg}, room=room)

# CLI helper to create DB


@app.cli.command('init-db')
def init_db():
    db.create_all()
    print('Initialized the database.')


if __name__ == '__main__':
    # create DB if not exists for convenience
    with app.app_context():
        if not os.path.exists(DB_PATH):
            db.create_all()
    # Configure basic logging so startup is visible
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get('PORT', 5000))
    print(
        "Starting SocketIO app on http://0.0.0.0:{}".format(port)
    )
    # use_reloader=False prevents the Flask reloader from creating
    # a second process during development
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=False,
    )
