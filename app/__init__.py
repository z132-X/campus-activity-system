import os

from flask import Flask

from .db import close_conn, init_db
from .routes import activity_bp, auth_bp, registration_bp


def create_app():
    app = Flask(__name__)
    # 会话密钥从环境变量读取，不硬编码；生产环境通过 .env 注入（.env 已被 .gitignore 排除）
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')

    app.teardown_appcontext(close_conn)

    app.register_blueprint(auth_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(registration_bp)

    init_db()
    return app
