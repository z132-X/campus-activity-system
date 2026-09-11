"""认证路由（REQ-01）。"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services.user_service import create_user, verify_user

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ok, msg = create_user(
            request.form.get('username'),
            request.form.get('password'),
            request.form.get('role'),
            request.form.get('display_name'),
        )
        flash(msg, 'success' if ok else 'error')
        if ok:
            return redirect(url_for('auth.login'))
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = verify_user(request.form.get('username'), request.form.get('password'))
        if user is None:
            flash('用户名或密码错误', 'error')
        else:
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['display_name']
            flash(f'欢迎，{user["display_name"]}', 'success')
            return redirect(url_for('activity.index'))
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
