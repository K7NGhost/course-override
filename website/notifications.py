from smtplib import SMTPException
from flask import current_app, flash
from flask_mail import Message
from .extensions import mail


def notify_student(item):
    """Send one email if SMTP is configured; otherwise just save the request."""
    if not current_app.config['MAIL_SERVER']:
        return

    message = Message(
        subject=f'Course override #{item.id}: {item.status}',
        recipients=[item.student.email],
        body=f'Hello {item.student_name},\n\nYour override request #{item.id} for {item.course_number} ({item.course_name}) is {item.status.lower()}.\n\nSign in to the Course Override Portal to view your request.\n\nOffice of the Registrar',
    )
    try:
        mail.send(message)
    except (SMTPException, OSError):
        current_app.logger.exception('Notification failed for request %s', item.id)
        flash('Your request was saved, but the email notification could not be sent.', 'warning')
