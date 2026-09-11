"""用户服务：注册与登录（REQ-01）。

对应工程意图：角色边界约束、密码哈希存储约束。
"""
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_conn, now

VALID_ROLES = ('student', 'teacher')


def create_user(username, password, role, display_name):
    """注册新用户。返回 (是否成功, 提示信息)。"""
    username = (username or '').strip()
    display_name = (display_name or '').strip()

    if not username or not password or not display_name:
        return False, '账号、密码与姓名均为必填'
    if role not in VALID_ROLES:
        return False, '身份不合法'
    if len(password) < 6:
        return False, '密码长度至少为 6 位'

    conn = get_conn()
    if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return False, '该账号已被注册'

    conn.execute(
        'INSERT INTO users (username, password_hash, role, display_name, created_at)'
        ' VALUES (?, ?, ?, ?, ?)',
        (username, generate_password_hash(password), role, display_name, now()),
    )
    conn.commit()
    return True, '注册成功，请登录'


def verify_user(username, password):
    """校验登录，成功返回用户行。

    失败时统一返回 None，不区分「账号不存在」与「密码错误」，避免账号枚举。
    """
    conn = get_conn()
    row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if row is None:
        return None
    if not check_password_hash(row['password_hash'], password):
        return None
    return row


def get_user(user_id):
    return get_conn().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
