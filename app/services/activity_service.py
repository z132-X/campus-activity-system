"""活动服务：浏览、发布与管理（REQ-02、REQ-05、REQ-06）。

对应工程意图：活动状态机、数据归属校验、时间逻辑校验。
"""
from ..db import get_conn, now


def _norm_time(value):
    """把 datetime-local 的 'YYYY-MM-DDTHH:MM' 统一成 'YYYY-MM-DD HH:MM'，便于比较与展示。"""
    return (value or '').strip().replace('T', ' ')


def list_published():
    """学生可见的活动列表，附带已报名人数。"""
    return get_conn().execute(
        '''
        SELECT a.*, u.display_name AS publisher_name,
               (SELECT COUNT(*) FROM registrations r
                 WHERE r.activity_id = a.id AND r.status = 'active') AS taken
        FROM activities a
        JOIN users u ON u.id = a.publisher_id
        WHERE a.status = 'published'
        ORDER BY a.start_time
        '''
    ).fetchall()


def get_visible(activity_id):
    """活动详情；已取消的活动对外不可见。"""
    return get_conn().execute(
        '''
        SELECT a.*, u.display_name AS publisher_name,
               (SELECT COUNT(*) FROM registrations r
                 WHERE r.activity_id = a.id AND r.status = 'active') AS taken
        FROM activities a
        JOIN users u ON u.id = a.publisher_id
        WHERE a.id = ? AND a.status != 'cancelled'
        ''',
        (activity_id,),
    ).fetchone()


def create_activity(teacher_id, form):
    """发布活动（REQ-05）。返回 (是否成功, 提示信息)。"""
    title = (form.get('title') or '').strip()
    location = (form.get('location') or '').strip()
    description = (form.get('description') or '').strip()
    start_time = _norm_time(form.get('start_time'))
    end_time = _norm_time(form.get('end_time'))
    deadline = _norm_time(form.get('deadline'))
    capacity_raw = (form.get('capacity') or '').strip()

    if not title or not location or not start_time or not end_time or not deadline:
        return False, '标题、地点、起止时间与报名截止均为必填'
    if not capacity_raw.isdigit() or int(capacity_raw) <= 0:
        return False, '容量必须为正整数'
    if start_time >= end_time:
        return False, '开始时间必须早于结束时间'
    if deadline > start_time:
        return False, '报名截止不能晚于活动开始时间'

    conn = get_conn()
    conn.execute(
        'INSERT INTO activities (title, description, location, start_time, end_time,'
        ' capacity, deadline, status, publisher_id, created_at)'
        " VALUES (?, ?, ?, ?, ?, ?, ?, 'published', ?, ?)",
        (title, description, location, start_time, end_time,
         int(capacity_raw), deadline, teacher_id, now()),
    )
    conn.commit()
    return True, '活动发布成功'


def list_by_teacher(teacher_id):
    return get_conn().execute(
        '''
        SELECT a.*,
               (SELECT COUNT(*) FROM registrations r
                 WHERE r.activity_id = a.id AND r.status = 'active') AS taken
        FROM activities a
        WHERE a.publisher_id = ?
        ORDER BY a.created_at DESC
        ''',
        (teacher_id,),
    ).fetchall()


def _owned(activity_id, teacher_id):
    """归属校验：教师只能操作自己发布的活动（工程意图约束 3）。"""
    return get_conn().execute(
        'SELECT * FROM activities WHERE id = ? AND publisher_id = ?',
        (activity_id, teacher_id),
    ).fetchone()


def close_activity(activity_id, teacher_id):
    if not _owned(activity_id, teacher_id):
        return False, '只能关闭自己发布的活动'
    conn = get_conn()
    conn.execute(
        "UPDATE activities SET status = 'closed' WHERE id = ? AND status = 'published'",
        (activity_id,),
    )
    conn.commit()
    return True, '报名已关闭'


def cancel_activity(activity_id, teacher_id):
    """取消活动：活动置为 cancelled，其有效报名同步失效，名额释放。"""
    if not _owned(activity_id, teacher_id):
        return False, '只能取消自己发布的活动'
    conn = get_conn()
    conn.execute("UPDATE activities SET status = 'cancelled' WHERE id = ?", (activity_id,))
    conn.execute(
        "UPDATE registrations SET status = 'cancelled'"
        " WHERE activity_id = ? AND status = 'active'",
        (activity_id,),
    )
    conn.commit()
    return True, '活动已取消，相关报名已同步失效'
