import os
import secrets
from pathlib import Path
import click
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_wtf.csrf import CSRFError
from .extensions import bootstrap, csrf, db, login_manager, mail, migrate


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    # A persisted local secret keeps development sessions stable across restarts.
    secret = os.getenv('SECRET_KEY')
    if not secret:
        secret_file = Path(app.instance_path) / 'secret.key'
        if not secret_file.exists():
            secret_file.write_text(secrets.token_hex(32), encoding='utf-8')
        secret = secret_file.read_text(encoding='utf-8').strip()
    app.config.from_mapping(
        SECRET_KEY=secret,
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///overrides.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
        MAX_CONTENT_LENGTH=64 * 1024,
        MAIL_SERVER=os.getenv('MAIL_SERVER') or None,
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME') or None,
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD') or None,
        MAIL_DEFAULT_SENDER=os.getenv('MAIL_USERNAME') or None,
        BOOTSTRAP_SERVE_LOCAL=True,
    )
    if test_config:
        app.config.update(test_config)
    for extension in (db, login_manager, mail, csrf, bootstrap):
        extension.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    from .models import User
    from .auth import auth
    from .views import views
    from .forms import LogoutForm
    app.register_blueprint(auth)
    app.register_blueprint(views)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id)) if user_id.isdigit() else None

    @app.context_processor
    def shared_forms():
        return {'logout_form': LogoutForm()}

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template('error.html', code=400, heading='Please refresh and try again', message='Your form session expired or its security token is missing.'), 400

    for code, heading, message in [
        (403, 'This page is restricted', 'You do not have permission to view this request or take this action.'),
        (404, 'We could not find that page', 'The page may have moved, or the request does not exist.'),
        (500, 'Something went wrong', 'We could not complete this action. Please try again shortly.'),
    ]:
        def handler(error, code=code, heading=heading, message=message):
            if code == 500:
                db.session.rollback()
            return render_template('error.html', code=code, heading=heading, message=message), code
        app.register_error_handler(code, handler)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.cli.command('create-staff')
    @click.option('--email', prompt=True)
    @click.option('--name', prompt=True)
    @click.password_option()
    def create_staff(email, name, password):
        """Create a staff reviewer; public registration always creates students."""
        from .forms import RegisterForm
        with app.test_request_context():
            form = RegisterForm(data={'email': email, 'name': name, 'password': password, 'confirm': password}, meta={'csrf': False})
            if not form.validate():
                raise click.ClickException(str(form.errors))
        email = email.strip().lower()
        if db.session.scalar(db.select(User).where(User.email == email)):
            raise click.ClickException('Email already registered. No account was changed.')
        user = User(email=email, name=name.strip(), is_staff=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo('Staff account created.')

    return app
