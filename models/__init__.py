# models/__init__.py
# Chuẩn hoá export: cho phép import trực tiếp từ package models
# Ví dụ: from models import db, Employee, Department, Role

from extensions import db

# --- Các model hệ phân quyền / modules ---
from .roles import Role
from .modules import Module
from .permissions import Permission
from .role_permissions import RolePermission

# --- Các model HR ---
from models.hr.employee_model import Employee, EmployeeRole
from models.hr.department_model import Department  # ⚠️ BỔ SUNG: export Department
from models.hr.hr_profiles import HRProfile
from models.hr_education_history import HREducationHistory
from models.hr_work_history import HRWorkHistory
from models.hr.dependent import HRDependent
from models.hr_salary_history import HRSalaryHistory
from .audit_logs import AuditLog

# --- Các model Dự toán ---
from .estimation import SkillGrade, WorkCategory, EstimationSheet, EstimationItem

# Tránh trùng lặp import HRProfile
__all__ = [
    "db",
    # Hệ phân quyền
    "Role",
    "Module",
    "Permission",
    "RolePermission",
    # HR
    "Employee",
    "EmployeeRole",
    "Department",
    "HRProfile",
    "HREducationHistory",
    "HRWorkHistory",
    "HRDependent",
    "HRSalaryHistory",
    # Audit
    "AuditLog",
    # Dự toán
    "SkillGrade",
    "WorkCategory",
    "EstimationSheet",
    "EstimationItem",
]
