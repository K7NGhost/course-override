import pytest
from sqlalchemy import inspect
from website.extensions import db, mail
from website.models import OverrideRequest, User


def test_migrations_build_schema(app):
    with app.app_context():
        assert {'user', 'override_request', 'alembic_version'} <= set(inspect(db.engine).get_table_names())


def test_auth_required_and_logout_uses_post(client, login):
    for path in ['/requests', '/requests/new', '/requests/1']:
        assert client.get(path).status_code == 302
    assert login().status_code == 302
    assert client.get('/logout').status_code == 405
    client.post('/logout')
    assert client.get('/requests').status_code == 302


def test_signup_hashes_password_and_cannot_create_staff(app, client):
    response = client.post('/sign-up', data={'name': 'New Student', 'email': 'NEW@example.com', 'password': 'LongPassword123', 'confirm': 'LongPassword123', 'is_staff': 'true'})
    assert response.status_code == 302
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == 'new@example.com'))
        assert not user.is_staff
        assert user.password_hash != 'LongPassword123'
        assert user.check_password('LongPassword123')


def test_duplicate_signup_and_wrong_password(client):
    data = {'name': 'Student', 'email': 'STUDENT@example.com', 'password': 'LongPassword123', 'confirm': 'LongPassword123'}
    assert b'already registered' in client.post('/sign-up', data=data).data
    assert b'Email or password is incorrect' in client.post('/login', data={'email': 'student@example.com', 'password': 'wrong'}).data


def test_valid_request_confirmation_and_email(app, client, login, payload):
    login()
    with app.app_context(), mail.record_messages() as messages:
        response = client.post('/requests/new', data=payload, follow_redirects=True)
        assert response.status_code == 200
        assert b'The course override has been submitted.' in response.data
        assert len(messages) == 1
        assert messages[0].recipients == ['student@example.com']
        item = db.session.scalar(db.select(OverrideRequest))
        assert item.status == 'Pending'
        assert item.justification == ''


@pytest.mark.parametrize('field,value', [('student_name', ''), ('student_name', '   '), ('student_id', ''), ('student_id', '123'), ('course_name', ''), ('course_number', ''), ('course_number', '<bad>'), ('justification', 'x' * 3001)])
def test_invalid_request_not_saved(app, client, login, payload, field, value):
    login()
    payload[field] = value
    response = client.post('/requests/new', data=payload)
    assert b'Please correct the highlighted fields' in response.data
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(OverrideRequest)) == 0


def test_ownership_and_staff_authorization(app, client, login, payload):
    login()
    client.post('/requests/new', data=payload)
    assert client.post('/requests/1/review', data={'status': 'Approved'}).status_code == 403
    client.post('/logout')
    login('other@example.com')
    assert client.get('/requests/1').status_code == 403
    assert b'Software Engineering' not in client.get('/requests').data
    client.post('/logout')
    login('staff@example.com')
    assert client.get('/requests/1').status_code == 200
    assert b'Software Engineering' in client.get('/requests').data
    assert client.post('/requests/1/review', data={'status': 'Invalid'}).status_code == 400
    with app.app_context(), mail.record_messages() as messages:
        assert client.post('/requests/1/review', data={'status': 'Approved'}).status_code == 302
        assert len(messages) == 1
        item = db.session.get(OverrideRequest, 1)
        assert item.status == 'Approved'
        assert item.reviewer.is_staff
        assert item.reviewed_at
    response = client.post('/requests/1/review', data={'status': 'Denied'}, follow_redirects=True)
    assert b'already been reviewed' in response.data
    with app.app_context():
        assert db.session.get(OverrideRequest, 1).status == 'Approved'


def test_email_failure_preserves_submission(app, client, login, payload, monkeypatch):
    login()
    def fail(*args, **kwargs):
        raise ConnectionError('Mail server unavailable')
    monkeypatch.setattr(mail, 'send', fail)
    response = client.post('/requests/new', data=payload, follow_redirects=True)
    assert b'email notification could not be sent' in response.data
    with app.app_context():
        assert db.session.get(OverrideRequest, 1)


def test_email_is_optional(app, client, login, payload, monkeypatch):
    app.config['MAIL_SERVER'] = None
    def unexpected_send(*args, **kwargs):
        pytest.fail('Email must not be sent without SMTP configuration')
    monkeypatch.setattr(mail, 'send', unexpected_send)
    login()
    response = client.post('/requests/new', data=payload, follow_redirects=True)
    assert b'The course override has been submitted.' in response.data
    assert b'Development mode' not in response.data
    with app.app_context():
        assert db.session.get(OverrideRequest, 1)


def test_csrf_is_enforced(app, client, payload):
    app.config['WTF_CSRF_ENABLED'] = True
    for path in ['/sign-up', '/login', '/logout', '/requests/new', '/requests/1/review']:
        response = client.post(path, data=payload)
        assert response.status_code == 400
        assert b'security token is missing' in response.data


def test_csrf_token_allows_login(app, client):
    import re
    app.config['WTF_CSRF_ENABLED'] = True
    page = client.get('/login')
    token = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', page.data).group(1).decode()
    response = client.post('/login', data={'email': 'student@example.com', 'password': 'StrongPassword123', 'csrf_token': token})
    assert response.status_code == 302
    assert client.get('/requests').status_code == 200


def test_404_and_500_pages(app, client):
    def crash():
        raise RuntimeError('Internal details should never be displayed')
    app.add_url_rule('/test-crash', view_func=crash)
    app.config['PROPAGATE_EXCEPTIONS'] = False
    assert client.get('/missing').status_code == 404
    assert b'We could not find that page' in client.get('/missing').data
    response = client.get('/test-crash')
    assert response.status_code == 500
    assert b'Something went wrong' in response.data
    assert b'Internal details' not in response.data


def test_justification_is_escaped(client, login, payload):
    login()
    payload['justification'] = '<script>alert(1)</script>'
    response = client.post('/requests/new', data=payload, follow_redirects=True)
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in response.data
    assert b'<script>alert(1)</script>' not in response.data


def test_create_staff_cli(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=['create-staff', '--email', 'reviewer@example.com', '--name', 'Reviewer'], input='StrongPassword123\nStrongPassword123\n')
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.scalar(db.select(User).where(User.email == 'reviewer@example.com')).is_staff
