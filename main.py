# app.py
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, session, flash, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, FileField, BooleanField, FloatField
from wtforms.validators import InputRequired, Email, Length, DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from functools import wraps
import os
from urllib.parse import quote_plus

# ------------------- App Setup -------------------
app = Flask(__name__, template_folder='template')

# Environment variables
db_user = os.environ.get("DB_USER")
db_password = quote_plus(os.environ.get("DB_PASSWORD"))  # encode special chars
db_name = os.environ.get("DB_NAME")
db_host = os.environ.get("DB_HOST", "localhost")
db_port = os.environ.get("DB_PORT", "5432")

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
db = SQLAlchemy(app)

# ------------------- Database Models -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(10))
    department = db.Column(db.String(50))
    amount_paid = db.Column(db.Float)
    balance = db.Column(db.Float, default=0.0)
    profile_pic = db.Column(db.LargeBinary)
    pic_mimetype = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    filetype = db.Column(db.String(50))
    year = db.Column(db.String(10))
    data = db.Column(db.LargeBinary)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    header = db.Column(db.String(400))
    content = db.Column(db.String(3000))

# ------------------- Forms -------------------
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=4)])
    submit = SubmitField('Login')

class ProfilePicForm(FlaskForm):
    profile_pic = FileField('Profile Picture')
    submit = SubmitField('Change Picture')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password')
    year = StringField('Year')
    department = StringField('Department')
    balance = FloatField('Balance', default=0.0)
    amount_paid = FloatField('Amount Paid', default=0.0)
    is_admin = BooleanField('Admin')
    submit = SubmitField('Save')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[InputRequired(), Length(min=4)])
    submit = SubmitField('Reset Password')

class UploadFile(FlaskForm):
    file = FileField('Choose a file', validators=[DataRequired()])
    studentYear = StringField('Student Year', validators=[DataRequired()])
    submit = SubmitField('Upload File')

# ------------------- Helper Functions -------------------
def create_user(username, email, password, year="", department="", balance=0.0, is_admin=False):
    if not User.query.filter_by(email=email).first():
        hashed_pwd = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_pwd,
                    year=year, department=department, balance=balance, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        print(f"✅ User {email} created! Admin={is_admin}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must login first!", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if not user or not user.is_admin:
            flash("Access denied — admin only area!", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------- Routes -------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("No account found with that email.", "danger")
        elif not check_password_hash(user.password, form.password.data):
            flash("Incorrect password. Please try again.", "danger")
        else:
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash(f"Welcome {user.username}!", "success")
            return redirect(url_for('admin_dashboard') if user.is_admin else url_for('dashboard'))
    elif form.is_submitted() and not form.validate():
        flash('Please fill in all required fields correctly.', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    form = ProfilePicForm()
    messages = Announcement.query.order_by(Announcement.id.desc()).all()

    if form.validate_on_submit() and form.profile_pic.data:
        file = form.profile_pic.data
        user.profile_pic = file.read()
        user.pic_mimetype = file.mimetype
        db.session.commit()
        flash("Profile picture updated!", "success")
    pic_data = base64.b64encode(user.profile_pic).decode('utf-8') if user.profile_pic else None
    files = File.query.order_by(File.id.desc()).all()
    return render_template('dashboard.html', user=user, form=form, pic_data=pic_data, files=files, messages=messages)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    files = File.query.order_by(File.id.asc()).all()
    messages = Announcement.query.order_by(Announcement.id.asc()).all()
    form = UploadFile()
    return render_template('admin_dashboard.html', users=users, form=form, files=files, messages=messages)

@app.route('/upload_file', methods=['POST'])
@login_required
@admin_required
def upload_file():
    form = UploadFile()
    if form.validate_on_submit():
        f = form.file.data
        new_file = File(
            filename=secure_filename(f.filename),
            filetype=f.content_type,
            year=form.studentYear.data,
            data=f.read()
        )
        db.session.add(new_file)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password') or "1234"
    year = request.form.get('year')
    department = request.form.get('department')
    balance = float(request.form.get('balance') or 0.0)
    amount = float(request.form.get('amount_paid') or 0.0)
    is_admin = bool(int(request.form.get('is_admin', 0)))

    if User.query.filter_by(email=email).first():
        flash("Email already exists!", "danger")
    else:
        hashed_pwd = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_pwd,
                    year=year, department=department, balance=balance, amount_paid=amount, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash(f"User {username} added!", "success")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['user_id']:
        flash("You cannot delete yourself!", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_file/<int:file_id>', methods=['POST'])
@login_required
@admin_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    db.session.delete(file)
    db.session.commit()
    flash(f"File '{file.filename}' deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    if new_password:
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash(f"Password for {user.username} reset successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/download/<int:id>')
@login_required
def download(id):
    file = File.query.get_or_404(id)
    return send_file(
        BytesIO(file.data),
        download_name=file.filename,
        as_attachment=True
    )

@app.route('/view/<int:id>')
@login_required
def view_file(id):
    file = File.query.get_or_404(id)
    return send_file(
        BytesIO(file.data),
        mimetype=file.filetype,
        download_name=file.filename
    )

@app.route('/preview/<int:id>')
@login_required
def preview_file(id):
    file = File.query.get_or_404(id)
    file_url = url_for('view_file', id=file.id)
    return render_template('preview.html', file=file, file_url=file_url)

@app.route("/announcement", methods=['GET', 'POST'])
@login_required
@admin_required
def announcement():
    title = request.form.get('mg-title') or "Announcement"
    message = request.form.get('announcement')
    announce = Announcement(header=title, content=message)
    db.session.add(announce)
    db.session.commit()
    flash(f"Message {title} has been uploaded", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def delete_message(message_id):
    message = Announcement.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash(f"Message '{message.header}' deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/editor')
@login_required
def editor():
    return render_template('editor.html')   # the page you want inside iframe

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

# ------------------- Initialize Database & Run -------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # creates tables in PostgreSQL
        if not User.query.filter_by(email="admin@example.com").first():
            create_user("Admin", "admin@example.com", "admin123", "N/A", "IT", 0.0, is_admin=True)
    app.run(debug=True)
