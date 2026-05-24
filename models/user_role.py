# models/user_role.py
from models import db


class UserRole(db.Model):
    __tablename__ = "UserRoles"

    EmployeeID = db.Column(db.Unicode(20), db.ForeignKey("Employees.EmployeeID"), primary_key=True)
    RoleID = db.Column(db.Integer, db.ForeignKey("Roles.RoleID"), primary_key=True)
    DepartmentCode = db.Column(db.Unicode(10), db.ForeignKey("Departments.DepartmentCode"), primary_key=True)


# ✅ Khai báo sau cùng để tránh vòng lặp import
from .employee import Employee
from .role import Role
from .departments import Department

UserRole.employee = db.relationship("Employee", backref="user_roles")
UserRole.role = db.relationship("Role", backref="user_roles")
UserRole.department = db.relationship("Department", backref="user_roles")
