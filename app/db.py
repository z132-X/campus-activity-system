"""数据层：SQLite 连接管理与建表。

SQL 只出现在这一层，服务层通过函数访问数据。
"""
import os
import sqlite3
from datetime import datetime

from flask import g

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')


def get_conn():
    """获取当前请求的连接（SQLite 不支持多线程共享，按请求创建）。"""
    if 'conn' not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        g.conn = conn
    return g.conn


def close_conn(e=None):
    conn = g.pop('conn', None)
    if conn is not None:
        conn.close()


def init_db():
    """按 schema.sql 建表（已存在则跳过）。"""
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
