from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app(config_object=None):
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # 載入設定
    if isinstance(config_object, str):
        app.config.from_pyfile(config_object)
    elif config_object:
        app.config.from_mapping(config_object)
    else:
        # 預設設定（可由 config.py/環境變數覆寫）
        os.makedirs('db', exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath('db/ais_data.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # 註冊路由（api.py 內會提供 register_routes）
    from . import api
    api.register_routes(app)

    return app