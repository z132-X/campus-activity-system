"""报名路由（REQ-03、REQ-04）。"""
from flask import Blueprint, flash, redirect, session, url_for

from ..services import registration_service
from ..utils import login_required

bp = Blueprint('registration', __name__, url_prefix='/reg')


@bp.route('/activity/<int:aid>/join', methods=['POST'])
@login_required('student')
def join(aid):
    try:
        registration_service.register(session['user_id'], aid)
        flash('报名成功', 'success')
    except registration_service.RuleError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('activity.detail', aid=aid))


@bp.route('/activity/<int:aid>/quit', methods=['POST'])
@login_required('student')
def quit_activity(aid):
    try:
        registration_service.cancel(session['user_id'], aid)
        flash('已取消报名', 'success')
    except registration_service.RuleError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('activity.detail', aid=aid))


@bp.route('/my')
@login_required('student')
def my():
    rows = registration_service.list_my(session['user_id'])
    return render_template('my_registrations.html', rows=rows)
