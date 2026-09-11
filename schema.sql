-- 校园活动管理系统 V1.0 数据库结构定义
-- 本文件是表结构的唯一依据；运行期数据文件 data.db 不纳入版本库（见 .gitignore）

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('student', 'teacher')),
    display_name  TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT    NOT NULL,
    description  TEXT,
    location     TEXT    NOT NULL,
    start_time   TEXT    NOT NULL,
    end_time     TEXT    NOT NULL,
    capacity     INTEGER NOT NULL CHECK (capacity > 0),
    deadline     TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'published'
                         CHECK (status IN ('published', 'closed', 'cancelled')),
    publisher_id INTEGER NOT NULL REFERENCES users(id),
    created_at   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS registrations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    activity_id INTEGER NOT NULL REFERENCES activities(id),
    status      TEXT    NOT NULL CHECK (status IN ('active', 'cancelled')),
    created_at  TEXT    NOT NULL,
    UNIQUE (user_id, activity_id)
);

CREATE INDEX IF NOT EXISTS idx_activities_status  ON activities(status);
CREATE INDEX IF NOT EXISTS idx_activities_publisher ON activities(publisher_id);
CREATE INDEX IF NOT EXISTS idx_registrations_activity ON registrations(activity_id, status);
CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(user_id);
