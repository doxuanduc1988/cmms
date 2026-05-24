from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from flask_login import UserMixin

db = SQLAlchemy()


class Employee(db.Model, UserMixin):  # ✅ kế thừa UserMixin
    __tablename__ = "Employees"

    EmployeeID = db.Column(db.String(20), primary_key=True)
    FullName = db.Column(db.Unicode(100), nullable=False)
    Username = db.Column(db.Unicode(50), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255))
    RoleID = db.Column(db.Integer, db.ForeignKey("Roles.RoleID"))
    role = db.relationship("Role")  # 👈 để truy cập employee.role.RoleName
    Status = db.Column(db.Unicode(50))
    Email = db.Column(db.Unicode(100))
    Phone = db.Column(db.String(20))
    Position = db.Column(db.Unicode(100))
    DepartmentCode = db.Column(db.String(10))

    department = db.relationship("Department", backref="employees")

    def get_id(self):
        return str(self.EmployeeID)


class Department(db.Model):
    __tablename__ = "Departments"

    DepartmentCode = db.Column(db.String(10), primary_key=True)
    DepartmentName = db.Column(db.Unicode(100), nullable=False)
    Description = db.Column(db.Unicode(255))


class Role(db.Model):
    __tablename__ = "Roles"
    RoleID = db.Column(db.Integer, primary_key=True)
    RoleName = db.Column(db.String(50), unique=True, nullable=False)


class Module(db.Model):
    __tablename__ = "Modules"
    ModuleID = db.Column(db.Integer, primary_key=True)
    ModuleCode = db.Column(db.String(50), unique=True, nullable=False)
    ModuleName = db.Column(db.String(100), nullable=False)

    permissions = db.relationship("Permission", backref="module", lazy=True)


class Permission(db.Model):
    __tablename__ = "Permissions"
    PermissionID = db.Column(db.Integer, primary_key=True)
    ModuleID = db.Column(db.Integer, db.ForeignKey("Modules.ModuleID"))
    Action = db.Column(db.String(50), nullable=False)


class RolePermission(db.Model):
    __tablename__ = "RolePermissions"
    RoleID = db.Column(db.Integer, db.ForeignKey("Roles.RoleID"), primary_key=True)
    PermissionID = db.Column(db.Integer, db.ForeignKey("Permissions.PermissionID"), primary_key=True)


class HRProfile(db.Model):
    __tablename__ = "HRProfiles"

    EmployeeID = db.Column(db.Unicode(20), primary_key=True)  # Dùng làm khóa chính, không còn quan hệ

    # Thông tin cá nhân
    FullName = db.Column(db.Unicode(100), nullable=False)
    Gender = db.Column(db.Unicode(10))
    DateOfBirth = db.Column(db.Date)
    PlaceOfBirth = db.Column(db.Unicode(100))
    Nationality = db.Column(db.Unicode(50))
    Ethnicity = db.Column(db.Unicode(50))
    MaritalStatus = db.Column(db.Unicode(50))

    # Thông tin liên hệ
    Email = db.Column(db.Unicode(100))
    Phone = db.Column(db.Unicode(20))
    EmergencyContactName = db.Column(db.Unicode(100))
    EmergencyContactPhone = db.Column(db.Unicode(20))
    ResidenceAddress = db.Column(db.Unicode(255))

    # CCCD / CMND
    IDNumber = db.Column(db.Unicode(20))  # CCCD/CMND
    IDIssuedDate = db.Column(db.Date)
    IDIssuedPlace = db.Column(db.Unicode(100))

    # Trình độ chuyên môn
    TechnicalLevel = db.Column(db.Unicode(100))  # Trình độ chuyên môn kỹ thuật
    Degree = db.Column(db.Unicode(100))
    Major = db.Column(db.Unicode(100))
    School = db.Column(db.Unicode(100))
    GraduationYear = db.Column(db.Unicode(10))

    # Công việc hiện tại
    JobPosition = db.Column(db.Unicode(100))  # Vị trí công việc
    DepartmentName = db.Column(db.Unicode(100))  # Phòng/Phân xưởng

    # Hợp đồng lao động
    ContractNumber = db.Column(db.Unicode(50))  # Số HĐLĐ
    ContractType = db.Column(db.Unicode(50))  # Loại HĐLĐ
    StartDate = db.Column(db.Date)  # Thời điểm bắt đầu làm việc
    EndDate = db.Column(db.Date)  # Thời điểm kết thúc

    # Lương & phụ cấp
    Salary = db.Column(db.Float)  # Mức lương hiện tại
    RegionAllowance = db.Column(db.Float)
    SalaryGrade = db.Column(db.Unicode(20))  # Phụ cấp khu vực
    PaymentMethod = db.Column(db.Unicode(50))
    BankAccount = db.Column(db.Unicode(50))

    # Bảo hiểm & thuế
    InsuranceNumber = db.Column(db.Unicode(20))  # Mã số BHXH
    InsuranceIssuedDate = db.Column(db.Date)
    TaxCode = db.Column(db.Unicode(20))  # Mã số thuế
    TaxIssuedDate = db.Column(db.Date)

    # Lịch sử, đào tạo, kỷ luật
    WorkHistory = db.Column(db.UnicodeText)  # Quá trình công tác
    SalaryHistory = db.Column(db.UnicodeText)  # Quá trình lương
    Training = db.Column(db.UnicodeText)  # Quá trình đào tạo
    Discipline = db.Column(db.UnicodeText)  # Quá trình kỷ luật

    # Nghỉ việc
    TerminationDate = db.Column(db.Date)
    TerminationReason = db.Column(db.Unicode(255))

    # Khác
    Dependents = db.Column(db.UnicodeText)  # Người phụ thuộc
    LeavePolicy = db.Column(db.Unicode(255))  # Chế độ nghỉ phép
    AnnualLeaveDays = db.Column(db.Float)  # Số ngày nghỉ trong năm
    LeaveReason = db.Column(db.Unicode(255))  # Lý do nghỉ
    OvertimeHours = db.Column(db.Float)  # Giờ làm thêm
    InsuranceStatus = db.Column(db.Unicode(50))  # Tình trạng BHXH
    WorkInjury = db.Column(db.UnicodeText)  # Tai nạn lao động
    Notes = db.Column(db.UnicodeText)

    # Lịch sử lương và công tác (tạm thời dùng dạng text cho đơn giản, có thể tách bảng riêng sau này)
