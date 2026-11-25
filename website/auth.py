from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .forms import LoginForm, LogoutForm, RegisterForm
from .models import User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.email == form.email.data.lower()))
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Welcome back. You are signed in.', 'success')
            return redirect(url_for('views.dashboard'))
        flash('Email or password is incorrect.', 'danger')
    return render_template('auth.html', form=form, register=False)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data.lower(), is_staff=False)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append('That email is already registered. Please sign in.')
        else:
            login_user(user)
            flash('Your account is ready. Submit your first override request.', 'success')
            return redirect(url_for('views.new_request'))
    return render_template('auth.html', form=form, register=True)


@auth.post('/logout')
@login_required
def logout():
    form = LogoutForm()
    if form.validate_on_submit():
        logout_user()
        flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))
