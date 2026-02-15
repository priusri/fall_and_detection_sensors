from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from extensions import db, login_manager
from models import User, Contact, FallEvent
from forms import RegistrationForm, LoginForm, ContactForm
from werkzeug.security import generate_password_hash, check_password_hash
from twilio_helper import send_fall_alert
import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
@main_bp.route("/home")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('main.login'))
    else:
        print("Registration Failed. Form Errors:", form.errors)
    return render_template('register.html', title='Register', form=form)

@main_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@main_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main_bp.route("/dashboard")
@login_required
def dashboard():
    latest_event = FallEvent.query.order_by(FallEvent.timestamp.desc()).first()
    return render_template('dashboard.html', title='Dashboard', latest_event=latest_event)

@main_bp.route("/api/fall_status")
@login_required
def fall_status():
    latest_event = FallEvent.query.order_by(FallEvent.timestamp.desc()).first()
    if latest_event:
        return jsonify({
            'timestamp': latest_event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'lat': latest_event.latitude,
            'long': latest_event.longitude,
            'status': latest_event.status
        })
    return jsonify({})

@main_bp.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    form = ContactForm()
    if form.validate_on_submit():
        phone = form.phone_number.data.strip()
        # Auto-format: If 10 digits, prepend +91
        if len(phone) == 10 and phone.isdigit():
            phone = "+91" + phone
            
        contact = Contact(name=form.name.data, phone_number=phone, owner=current_user)
        db.session.add(contact)
        db.session.commit()
        flash('Emergency contact added!', 'success')
        return redirect(url_for('main.settings'))
    
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('settings.html', title='Settings', form=form, contacts=contacts)

@main_bp.route("/settings/contact/<int:contact_id>/delete", methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.owner != current_user:
        abort(403)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact has been deleted!', 'success')
    return redirect(url_for('main.settings'))

# API Endpoint for Hardware
@main_bp.route("/api/fall", methods=['POST'])
def receive_fall_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    lat = data.get('lat')
    long = data.get('long') # Avoid reserved keyword
    device_id = data.get('device_id')
    
    if lat is None or long is None:
        return jsonify({'error': 'Missing coordinates'}), 400

    # Record event
    # Ensure floats
    try:
        lat = float(lat)
        long = float(long)
    except ValueError:
         return jsonify({'error': 'Invalid coordinates format'}), 400

    new_fall = FallEvent(latitude=lat, longitude=long, device_id=device_id, status='Active')
    db.session.add(new_fall)
    db.session.commit()

    # Trigger Twilio for all users (or filtered by device_id if mapped)
    # For simplicity, alerting ALL users' contacts. In real app, map device_id to user.
    # Assuming single user system for now or broadcast.
    
    # Better approach: If device_id is linked to a user, alert that user's contacts.
    # For now, let's alert all contacts in DB (Simpler for demo)
    contacts = Contact.query.all()
    alert_count = 0
    for contact in contacts:
        if send_fall_alert(lat, long, contact.phone_number, contact.name):
            alert_count += 1
            
    return jsonify({'message': 'Fall detected and recorded.', 'alerts_sent': alert_count}), 201
