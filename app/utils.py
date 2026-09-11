"""通用工具：登录与身份校验装饰器。"""
from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(role=None):
    """要求登录；指定 role 时同时校验身份。

    校验在服务端强制，不依赖页面是否隐藏入口（工程意图约束 1）。
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('请先登录', 'error')
                return redirect(url_for('auth.login'))
            if role and session.get('role') != role:
                flash('当前身份无权访问该功能', 'error')
                return redirect(url_for('activity.index'))
            return view(*args, **kwargs)
        return wrapper
    return decorator
