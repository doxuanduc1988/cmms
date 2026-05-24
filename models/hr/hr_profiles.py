from extensions import db
from .job_position_model import JobPosition


class HRProfile(db.Model):
    __tablename__ = "HRProfiles"

    EmployeeID = db.Column(db.Unicode(20), primary_key=True)
    FullName = db.Column(db.Unicode(100), nullable=False)
    Gender = db.Column(db.Unicode(10))
    StaffCode = db.Column(db.Unicode(20))
    Nationality = db.Column(db.Unicode(50))
    Ethnicity = db.Column(db.Unicode(50))
    ResidenceAddress = db.Column(db.Unicode(255))
    DateOfBirth = db.Column(db.Date)
    PlaceOfBirth = db.Column(db.Unicode(100))
    Email = db.Column(db.Unicode(100))
    Phone = db.Column(db.Unicode(20))
    EmergencyContactName = db.Column(db.Unicode(100))
    EmergencyContactPhone = db.Column(db.Unicode(20))

    Photo = db.Column(db.String(255), nullable=True)

    IDNumber = db.Column(db.Unicode(20))  # CCCD/CMND
    IDIssuedDate = db.Column(db.Date)
    IDIssuedPlace = db.Column(db.Unicode(100))

    InsuranceNumber = db.Column(db.Unicode(20))  # Mã số BHXH
    InsuranceIssuedDate = db.Column(db.Date)

    TaxCode = db.Column(db.Unicode(20))  # Mã số thuế
    TaxIssuedDate = db.Column(db.Date)

    TechnicalLevel = db.Column(db.Unicode(100))  # Trình độ chuyên môn kỹ thuật
    JobPositionID = db.Column(db.Integer, db.ForeignKey("JobPositions.JobPositionID"), nullable=True)
    JobPosition = db.relationship("JobPosition", backref="hr_profiles", lazy=True)

    # JobPosition = db.Column(db.Unicode(100))        # Vị trí công việc
    DepartmentCode = db.Column(db.String(10), db.ForeignKey("Departments.DepartmentCode"))
    CrewID = db.Column(db.Integer, nullable=True)  # <-- Bổ sung trường này

    ContractNumber = db.Column(db.Unicode(50))  # Số HĐLĐ
    ContractType = db.Column(db.Unicode(50))  # Loại HĐLĐ
    StartDate = db.Column(db.Date)  # Thời điểm bắt đầu làm việc
    EndDate = db.Column(db.Date)    # Thời điểm kết thúc HĐLĐ

    Salary = db.Column(db.Float)  # Mức lương hiện tại
    RegionAllowance = db.Column(db.Float)  # Phụ cấp khu vực
    SalaryGrade = db.Column(db.Unicode(50))  # Ngạch/Bậc lương
    PaymentMethod = db.Column(db.Unicode(50))  # Phương thức thanh toán

    SalaryHistory = db.Column(db.UnicodeText)  # Quá trình lương
    WorkHistory = db.Column(db.UnicodeText)  # Quá trình công tác
    Dependents = db.Column(db.UnicodeText)  # Người phụ thuộc
    BankAccount = db.Column(db.Unicode(50))  # Tài khoản nhận lương

    LeavePolicy = db.Column(db.Unicode(255))  # Chế độ nghỉ phép
    AnnualLeaveDays = db.Column(db.Float)  # Số ngày nghỉ trong năm
    LeaveReason = db.Column(db.Unicode(255))  # Lý do nghỉ

    OvertimeHours = db.Column(db.Float)  # Giờ làm thêm
    InsuranceStatus = db.Column(db.Unicode(50))  # Tình trạng BHXH

    Training = db.Column(db.UnicodeText)  # Đào tạo
    Discipline = db.Column(db.UnicodeText)  # Kỷ luật
    WorkInjury = db.Column(db.UnicodeText)  # Tai nạn lao động

    TerminationDate = db.Column(db.Date)  # Thời điểm nghỉ việc
    TerminationReason = db.Column(db.Unicode(255))  # Lý do thôi việc
    Notes = db.Column(db.UnicodeText)  # Ghi chú

    # Thêm quan hệ
    department = db.relationship("Department", backref="hr_profiles")
