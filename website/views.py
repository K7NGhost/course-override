from datetime import datetime, timezone
from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from .extensions import db
from .forms import OverrideForm, ReviewForm
from .models import OverrideRequest
from .notifications import notify_student

views = Blueprint('views', __name__)


@views.get('/')
def index():
    return redirect(url_for('views.dashboard') if current_user.is_authenticated else url_for('auth.login'))


@views.get('/requests')
@login_required
def dashboard():
    query = db.select(OverrideRequest)
    if not current_user.is_staff:
        query = query.where(OverrideRequest.user_id == current_user.id)
    items = db.session.scalars(query.order_by(OverrideRequest.created_at.desc())).all()
    return render_template('dashboard.html', items=items)


@views.route('/requests/new', methods=['GET', 'POST'])
@login_required
def new_request():
    form = OverrideForm()
    if form.validate_on_submit():
        item = OverrideRequest(
            user_id=current_user.id,
            student_name=form.student_name.data,
            student_id=form.student_id.data,
            course_name=form.course_name.data,
            course_number=form.course_number.data,
            justification=form.justification.data,
        )
        db.session.add(item)
        db.session.commit()
        flash('The course override has been submitted.', 'success')
        notify_student(item)
        return redirect(url_for('views.detail', request_id=item.id))
    if not form.is_submitted():
        form.student_name.data = current_user.name
    return render_template('request_form.html', form=form)


@views.get('/requests/<int:request_id>')
@login_required
def detail(request_id):
    item = db.get_or_404(OverrideRequest, request_id)
    if item.user_id != current_user.id and not current_user.is_staff:
        abort(403)
    return render_template('detail.html', item=item, form=ReviewForm())


@views.post('/requests/<int:request_id>/review')
@login_required
def review(request_id):
    if not current_user.is_staff:
        abort(403)
    item = db.get_or_404(OverrideRequest, request_id)
    form = ReviewForm()
    if not form.validate_on_submit():
        return render_template('detail.html', item=item, form=form), 400
    # Conditional update prevents a second reviewer from overwriting a decision.
    result = db.session.execute(
        db.update(OverrideRequest)
        .where(OverrideRequest.id == item.id, OverrideRequest.status == 'Pending')
        .values(
            status=form.status.data,
            reviewed_by=current_user.id,
            reviewed_at=datetime.now(timezone.utc),
        )
    )
    if result.rowcount != 1:
        db.session.rollback()
        flash('This request has already been reviewed.', 'warning')
    else:
        db.session.commit()
        flash('Decision saved.', 'success')
        notify_student(item)
    return redirect(url_for('views.detail', request_id=item.id))
