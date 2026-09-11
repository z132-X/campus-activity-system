"""活动路由（REQ-02、REQ-05、REQ-06）。"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services import activity_service, registration_service
from ..utils import login_required

bp = Blueprint('activity', __name__)


@bp.route('/')
@login_required()
def index():
    acts = activity_service.list_published()
    return render_template('activity_list.html', acts=acts)


@bp.route('/activity/<int:aid>')
@login_required()
def detail(aid):
    act = activity_service.get_visible(aid)
    if act is None:
        flash('活动不存在或已取消', 'error')
        return redirect(url_for('activity.index'))

    mine = None
    if session.get('role') == 'student':
        mine = registration_service.get_mine(session['user_id'], aid)
    return render_template('activity_detail.html', act=act, mine=mine)


@bp.route('/activity/new', methods=['GET', 'POST'])
@login_required('teacher')
def publish():
    if request.method == 'POST':
        ok, msg = activity_service.create_activity(session['user_id'], request.form)
        flash(msg, 'success' if ok else 'error')
        if ok:
            return redirect(url_for('activity.mine'))
    return render_template('publish.html')


@bp.route('/teacher/activities')
@login_required('teacher')
def mine():
    acts = activity_service.list_by_teacher(session['user_id'])
    return render_template('teacher_activities.html', acts=acts)


@bp.route('/activity/<int:aid>/close', methods=['POST'])
@login_required('teacher')
def close(aid):
    ok, msg = activity_service.close_activity(aid, session['user_id'])
    flash(msg, 'success' if ok else 'error')
    return redirect(url_for('activity.mine'))


@bp.route('/activity/<int:aid>/cancel', methods=['POST'])
@login_required('teacher')
def cancel(aid):
    ok, msg = activity_service.cancel_activity(aid, session['user_id'])
    flash(msg, 'success' if ok else 'error')
    return redirect(url_for('activity.mine'))


@bp.route('/activity/<int:aid>/participants')
@login_required('teacher')
def participants(aid):
    act, rows = registration_service.participants(aid, session['user_id'])
    if act is None:
        flash('活动不存在或无权查看该活动名单', 'error')
        return redirect(url_for('activity.mine'))
    return render_template('participants.html', act=act, rows=rows)
