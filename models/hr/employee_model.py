# models/employees.py
from extensions import db
from flask_login import UserMixin
from models.roles import Role


class EmployeeRole(db.Model):
    __tablename__ = "EmployeeRoles"
    EmployeeID = db.Column(db.String(20), db.ForeignKey("Employees.EmployeeID"), primary_key=True)
    RoleID = db.Column(db.Integer, db.ForeignKey("Roles.RoleID"), primary_key=True)


class Employee(UserMixin, db.Model):
    __tablename__ = "Employees"

    EmployeeID = db.Column(db.String(20), primary_key=True)
    FullName = db.Column(db.Unicode(100), nullable=False)
    Username = db.Column(db.String(50), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    # RoleID = db.Column(db.Integer, db.ForeignKey("Roles.RoleID"))  # ⛔ DEPRECATED
    DepartmentCode = db.Column(db.String(10))
    Status = db.Column(db.String(20))

    # ✅ Đổi sang quan hệ many-to-many
    roles = db.relationship("Role", secondary="EmployeeRoles", backref="employees", lazy="dynamic")

    def get_id(self):
        return self.EmployeeID

    @property
    def is_active(self):
        return self.Status.lower() == "active"
