from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_staff = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class OverrideRequest(db.Model):
    __table_args__ = (db.CheckConstraint("status IN ('Pending', 'Approved', 'Denied')", name='valid_status'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(9), nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    course_number = db.Column(db.String(20), nullable=False)
    justification = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    student = db.relationship(User, foreign_keys=[user_id])
    reviewer = db.relationship(User, foreign_keys=[reviewed_by])
