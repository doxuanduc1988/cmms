from extensions import db


class Role(db.Model):
    __tablename__ = "Roles"

    RoleID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RoleName = db.Column(db.Unicode(50), nullable=False, unique=True)
    Description = db.Column(db.Unicode(255))
    # role = db.relationship("models.roles.Role", backref="employees")  # ⛔ KHÔNG CẦN, gây lỗi!
