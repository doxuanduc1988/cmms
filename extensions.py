# extensions.py
# Khởi tạo các extension dùng chung cho toàn bộ ứng dụng.
# Các module khác import từ đây để tránh circular import.

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
bcrypt = Bcrypt()
