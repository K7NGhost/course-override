from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, SelectChoice
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp


def strip(value):
    return value.strip() if value else value


class LoginForm(FlaskForm):
    email = StringField('Email address', filters=[strip], validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField('Password', validators=[DataRequired(), Length(max=128)])
    submit = SubmitField('Sign in')


class RegisterForm(LoginForm):
    name = StringField('Full name', filters=[strip], validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=10, max=128)])
    confirm = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create account')


class OverrideForm(FlaskForm):
    student_name = StringField('Student name', filters=[strip], validators=[DataRequired(), Length(min=2, max=100)])
    student_id = StringField('Student ID', filters=[strip], validators=[DataRequired(), Regexp(r'^V\d{8}$', message='Use V followed by eight digits, for example V01234567.')])
    course_name = StringField('Course name', filters=[strip], validators=[DataRequired(), Length(min=2, max=150)])
    course_number = StringField('Course number', filters=[strip, lambda v: v.upper() if v else v], validators=[DataRequired(), Regexp(r'^[A-Z]{2,4} ?\d{3}[A-Z]?$', message='Use a subject and three-digit number, for example CMSC 301.')])
    justification = TextAreaField('Justification', filters=[strip], validators=[Optional(), Length(max=3000)])
    submit = SubmitField('Submit override request')


class ReviewForm(FlaskForm):
    status = SelectField('Decision', choices=[SelectChoice('Approved', 'Approve request'), SelectChoice('Denied', 'Deny request')], validators=[DataRequired()])
    submit = SubmitField('Save decision')


class LogoutForm(FlaskForm):
    submit = SubmitField('Sign out')
