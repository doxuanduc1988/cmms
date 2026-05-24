from extensions import db


class RolePermission(db.Model):
    __tablename__ = "RolePermissions"

    RoleID = db.Column(db.Integer, db.ForeignKey("Roles.RoleID"), primary_key=True)
    PermissionID = db.Column(db.Integer, db.ForeignKey("Permissions.PermissionID"), primary_key=True)
