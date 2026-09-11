"""报名服务：报名、取消与查询（REQ-03、REQ-04）。

对应工程意图：报名五重校验、截止后不可取消、取消用状态标记而非物理删除。
"""
from ..db import get_conn, now


class RuleError(Exception):
    """业务规则被违反时抛出，由路由层捕获并提示。"""


def register(user_id, activity_id):
    """学生报名，按设计执行五重校验。

    顺序与 docs/03-软件设计.md 流程一一致：
    活动存在且未取消 → 报名未关闭 → 未过截止 → 名额未满 → 未重复报名。
    """
    conn = get_conn()
    act = conn.execute('SELECT * FROM activities WHERE id = ?', (activity_id,)).fetchone()

    if act is None or act['status'] == 'cancelled':
        raise RuleError('活动不存在或已取消')
    if act['status'] == 'closed':
        raise RuleError('该活动报名已关闭')
    if now() > act['deadline']:
        raise RuleError('已超过报名截止时间，无法报名')

    taken = conn.execute(
        "SELECT COUNT(*) AS c FROM registrations"
        " WHERE activity_id = ? AND status = 'active'",
        (activity_id,),
    ).fetchone()['c']
    if taken >= act['capacity']:
        raise RuleError('名额已满，报名失败')

    row = conn.execute(
        'SELECT * FROM registrations WHERE user_id = ? AND activity_id = ?',
        (user_id, activity_id),
    ).fetchone()

    if row:
        if row['status'] == 'active':
            raise RuleError('你已报名该活动，不可重复报名')
        # 曾取消过：复用记录，避免被 UNIQUE 约束阻塞（对应设计决策 2）
        conn.execute(
            "UPDATE registrations SET status = 'active', created_at = ? WHERE id = ?",
            (now(), row['id']),
        )
    else:
        conn.execute(
            'INSERT INTO registrations (user_id, activity_id, status, created_at)'
            " VALUES (?, ?, 'active', ?)",
            (user_id, activity_id, now()),
        )
    conn.commit()


def cancel(user_id, activity_id):
    """取消报名。截止后不可取消（工程意图约束 4）。"""
    conn = get_conn()
    act = conn.execute('SELECT * FROM activities WHERE id = ?', (activity_id,)).fetchone()
    if act is None:
        raise RuleError('活动不存在')
    if now() > act['deadline']:
        raise RuleError('已超过报名截止时间，无法取消')

    row = conn.execute(
        'SELECT * FROM registrations WHERE user_id = ? AND activity_id = ?',
        (user_id, activity_id),
    ).fetchone()
    if row is None or row['status'] != 'active':
        raise RuleError('你尚未报名该活动')

    conn.execute("UPDATE registrations SET status = 'cancelled' WHERE id = ?", (row['id'],))
    conn.commit()


def get_mine(user_id, activity_id):
    return get_conn().execute(
        'SELECT * FROM registrations WHERE user_id = ? AND activity_id = ?',
        (user_id, activity_id),
    ).fetchone()


def list_my(user_id):
    return get_conn().execute(
        '''
        SELECT a.*, r.status AS reg_status, r.created_at AS reg_time
        FROM registrations r
        JOIN activities a ON a.id = r.activity_id
        WHERE r.user_id = ?
        ORDER BY a.start_time
        ''',
        (user_id,),
    ).fetchall()


def participants(activity_id, teacher_id):
    """教师查看报名名单，含归属校验。越权返回 None。"""
    conn = get_conn()
    act = conn.execute(
        'SELECT * FROM activities WHERE id = ? AND publisher_id = ?',
        (activity_id, teacher_id),
    ).fetchone()
    if act is None:
        return None, []

    rows = conn.execute(
        '''
        SELECT u.display_name, u.username, r.status, r.created_at
        FROM registrations r JOIN users u ON u.id = r.user_id
        WHERE r.activity_id = ?
        ORDER BY r.created_at
        ''',
        (activity_id,),
    ).fetchall()
    return act, rows
