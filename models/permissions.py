from extensions import db
from models.modules import Module  # hoặc từ nơi bạn định nghĩa class Module


class Permission(db.Model):
    __tablename__ = "Permissions"

    PermissionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ModuleID = db.Column(db.Integer, db.ForeignKey("Modules.ModuleID"), nullable=False)
    Action = db.Column(db.Unicode(50), nullable=False)
    Description = db.Column(db.Unicode(255))

    # ✅ Quan hệ ngược đến bảng Modules
    module = db.relationship("Module", backref="permissions")

    __table_args__ = (db.UniqueConstraint("ModuleID", "Action", name="uq_module_action"),)
