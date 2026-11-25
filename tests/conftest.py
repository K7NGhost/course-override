import pytest
from flask_migrate import upgrade
from website import create_app
from website.extensions import db
from website.models import User


@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only-secret', 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{tmp_path / "test.db"}', 'WTF_CSRF_ENABLED': False, 'MAIL_SERVER': 'smtp.example.com', 'MAIL_DEFAULT_SENDER': 'registrar@example.com', 'MAIL_SUPPRESS_SEND': True})
    with app.app_context():
        upgrade()
        for email, staff in [('student@example.com', False), ('other@example.com', False), ('staff@example.com', True)]:
            user = User(email=email, name=email.split('@')[0].title(), is_staff=staff)
            user.set_password('StrongPassword123')
            db.session.add(user)
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def sign_in(email='student@example.com'):
        return client.post('/login', data={'email': email, 'password': 'StrongPassword123'})
    return sign_in


@pytest.fixture
def payload():
    return {'student_name': 'Alex Student', 'student_id': 'V01234567', 'course_name': 'Software Engineering', 'course_number': 'CMSC 355', 'justification': ''}
