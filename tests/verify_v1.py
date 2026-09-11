"""校园活动管理系统 V1.0 验证脚本。

覆盖 REQ-01~REQ-06 的主要业务过程、关键业务规则与异常情况。
运行：python tests/verify_v1.py

说明：脚本每次运行会重建 data.db，保证结果可复现；data.db 不纳入版本库。
"""
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

DB = os.path.join(BASE, 'data.db')
if os.path.exists(DB):
    os.remove(DB)

from app import create_app  # noqa: E402

app = create_app()
app.config['TESTING'] = True

RESULTS = []


def check(test_id, name, ok, detail=''):
    RESULTS.append((test_id, name, bool(ok), detail))


def query(sql, args=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return rows


def has_text(resp, text):
    return text.encode('utf-8') in resp.data


def reg(c, username, password, role, name):
    return c.post('/auth/register', data={
        'username': username, 'password': password,
        'role': role, 'display_name': name,
    }, follow_redirects=True)


def login(c, username, password):
    return c.post('/auth/login', data={'username': username, 'password': password},
                  follow_redirects=True)


def publish(c, **over):
    data = {
        'title': '秋季校园运动会', 'location': '中心体育场',
        'start_time': '2026-10-20 09:00', 'end_time': '2026-10-20 17:00',
        'deadline': '2026-10-18 18:00', 'capacity': '2', 'description': '一年一度',
    }
    data.update(over)
    return c.post('/activity/new', data=data, follow_redirects=True)


with app.test_client() as c:
    # ========== TEST-01 注册与登录（REQ-01） ==========
    r = reg(c, 'stu1', '123456', 'student', '张同学')
    check('TEST-01', '学生注册成功', has_text(r, '注册成功'))

    row = query("SELECT password_hash FROM users WHERE username='stu1'")[0]
    ph = row['password_hash']
    check('TEST-01', '密码以哈希存储且非明文', ph != '123456' and len(ph) > 30,
          f'存储值前 20 位：{ph[:20]}...')

    r = reg(c, 'stu1', '123456', 'student', '张同学')
    check('TEST-01', '重复账号注册被拒绝', has_text(r, '该账号已被注册'))

    r = reg(c, 't1', '123456', 'teacher', '李老师')
    check('TEST-01', '教师注册成功', has_text(r, '注册成功'))

    r = login(c, 'stu1', 'wrongpass')
    check('TEST-01', '错误密码无法登录', has_text(r, '用户名或密码错误'))

    r = login(c, 'stu1', '123456')
    check('TEST-01', '正确凭证登录成功', has_text(r, '欢迎'))

    c.get('/auth/logout', follow_redirects=True)
    r = c.get('/', follow_redirects=False)
    check('TEST-01', '未登录访问功能页被拦截', r.status_code == 302,
          f'状态码 {r.status_code}')

    # ========== TEST-05 教师发布活动（REQ-05） ==========
    login(c, 't1', '123456')
    r = publish(c)
    check('TEST-05', '活动发布成功', has_text(r, '活动发布成功'))

    r = publish(c, title='', location='')
    check('TEST-05', '必填项缺失被拒绝', has_text(r, '均为必填'))

    r = publish(c, start_time='2026-10-20 17:00', end_time='2026-10-20 09:00')
    check('TEST-05', '开始时间晚于结束时间被拒绝', has_text(r, '开始时间必须早于结束时间'))

    r = publish(c, deadline='2026-10-21 10:00')
    check('TEST-05', '报名截止晚于活动开始被拒绝', has_text(r, '报名截止不能晚于活动开始时间'))

    r = publish(c, capacity='0')
    check('TEST-05', '容量非正数被拒绝', has_text(r, '容量必须为正整数'))

    aid = query("SELECT id FROM activities WHERE title='秋季校园运动会'")[0]['id']

    c.get('/auth/logout', follow_redirects=True)
    login(c, 'stu1', '123456')
    r = c.get('/activity/new', follow_redirects=True)
    check('TEST-05', '学生身份无法进入发布页', has_text(r, '无权访问'))

    # ========== TEST-02 活动浏览（REQ-02） ==========
    r = c.get('/')
    check('TEST-02', '活动列表展示已发布活动', has_text(r, '秋季校园运动会'))

    r = c.get(f'/activity/{aid}')
    check('TEST-02', '活动详情展示剩余名额', has_text(r, '剩余 2'))

    # ========== TEST-03 学生报名（REQ-03） ==========
    r = c.post(f'/reg/activity/{aid}/join', follow_redirects=True)
    check('TEST-03', '学生报名成功', has_text(r, '报名成功'))

    r = c.post(f'/reg/activity/{aid}/join', follow_redirects=True)
    check('TEST-03', '重复报名被拒绝', has_text(r, '不可重复报名'))

    c.get('/auth/logout', follow_redirects=True)
    reg(c, 'stu2', '123456', 'student', '王同学')
    login(c, 'stu2', '123456')
    c.post(f'/reg/activity/{aid}/join', follow_redirects=True)

    c.get('/auth/logout', follow_redirects=True)
    reg(c, 'stu3', '123456', 'student', '赵同学')
    login(c, 'stu3', '123456')
    r = c.post(f'/reg/activity/{aid}/join', follow_redirects=True)
    check('TEST-03', '名额已满时报名被拒绝', has_text(r, '名额已满'))

    # 报名已过截止的活动
    c.get('/auth/logout', follow_redirects=True)
    login(c, 't1', '123456')
    publish(c, title='过期讲座', start_time='2026-09-01 09:00',
            end_time='2026-09-01 11:00', deadline='2026-09-01 08:00', capacity='10')
    expired_id = query("SELECT id FROM activities WHERE title='过期讲座'")[0]['id']
    c.get('/auth/logout', follow_redirects=True)
    login(c, 'stu3', '123456')
    r = c.post(f'/reg/activity/{expired_id}/join', follow_redirects=True)
    check('TEST-03', '已过报名截止时报名被拒绝', has_text(r, '已超过报名截止时间'))

    # ========== TEST-04 取消报名（REQ-04） ==========
    # stu1 取消后名额释放，stu3 应可报上
    c.get('/auth/logout', follow_redirects=True)
    login(c, 'stu1', '123456')
    r = c.post(f'/reg/activity/{aid}/quit', follow_redirects=True)
    check('TEST-04', '取消报名成功', has_text(r, '已取消报名'))

    st = query("SELECT status FROM registrations WHERE user_id="
               "(SELECT id FROM users WHERE username='stu1') AND activity_id=?", (aid,))[0]
    check('TEST-04', '取消采用状态标记而非物理删除', st['status'] == 'cancelled',
          f"记录状态 {st['status']}")

    c.get('/auth/logout', follow_redirects=True)
    login(c, 'stu3', '123456')
    r = c.post(f'/reg/activity/{aid}/join', follow_redirects=True)
    check('TEST-04', '取消后名额被释放，他人可报名', has_text(r, '报名成功'))

    # 截止后不可取消：把活动 deadline 改到过去
    query_conn = sqlite3.connect(DB)
    query_conn.execute("UPDATE activities SET deadline='2020-01-01 08:00' WHERE id=?", (aid,))
    query_conn.commit()
    query_conn.close()
    r = c.post(f'/reg/activity/{aid}/quit', follow_redirects=True)
    check('TEST-04', '已过截止时间后取消被拒绝', has_text(r, '已超过报名截止时间，无法取消'))

    # ========== TEST-06 教师管理活动（REQ-06） ==========
    c.get('/auth/logout', follow_redirects=True)
    login(c, 't1', '123456')
    r = c.get(f'/activity/{aid}/participants')
    acts_participants_ok = has_text(r, '张同学') or has_text(r, '赵同学')
    check('TEST-06', '教师可查看报名名单', acts_participants_ok)

    cnt = query("SELECT COUNT(*) c FROM registrations WHERE activity_id=? AND status='active'",
                (aid,))[0]['c']
    check('TEST-06', '名单人数与有效报名数一致', cnt == 2, f'有效报名 {cnt} 人')

    # 越权：另一位教师尝试取消 t1 的活动
    c.get('/auth/logout', follow_redirects=True)
    reg(c, 't2', '123456', 'teacher', '陈老师')
    login(c, 't2', '123456')
    r = c.post(f'/activity/{aid}/cancel', follow_redirects=True)
    check('TEST-06', '教师无法操作他人活动', has_text(r, '只能取消自己发布的活动'))

    # 取消活动后学生端不可见
    c.get('/auth/logout', follow_redirects=True)
    login(c, 't1', '123456')
    c.post(f'/activity/{aid}/cancel', follow_redirects=True)
    c.get('/auth/logout', follow_redirects=True)
    login(c, 'stu1', '123456')
    r = c.get('/')
    check('TEST-06', '活动取消后学生端不可见', not has_text(r, '秋季校园运动会'))


# ========== 输出汇总 ==========
print('=' * 66)
print('校园活动管理系统 V1.0 验证结果')
print('=' * 66)

groups = {}
for tid, name, ok, detail in RESULTS:
    groups.setdefault(tid, []).append((name, ok, detail))

total = passed = 0
for tid in sorted(groups):
    items = groups[tid]
    ok_count = sum(1 for _, ok, _ in items if ok)
    total += len(items)
    passed += ok_count
    print(f'\n{tid}  ({ok_count}/{len(items)} 通过)')
    for name, ok, detail in items:
        mark = 'PASS' if ok else 'FAIL'
        line = f'  [{mark}] {name}'
        if detail:
            line += f'  —— {detail}'
        print(line)

print('\n' + '=' * 66)
print(f'合计：{passed}/{total} 项通过')
print('=' * 66)
sys.exit(0 if passed == total else 1)
