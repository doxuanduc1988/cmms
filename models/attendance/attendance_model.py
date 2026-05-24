# models/attendance.py
from extensions import db
from models.hr.hr_profiles import HRProfile  # import bảng HRProfiles


class Attendance(db.Model):
    __tablename__ = "Attendance"

    AttendanceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    Date = db.Column(db.Date, nullable=False)
    ShiftID = db.Column(db.Integer, nullable=False)
    CrewID = db.Column(db.Integer, nullable=True)
    DepartmentCode = db.Column(db.String(10), nullable=False)  # Đã chuẩn hóa
    CheckInTime = db.Column(db.Time, nullable=True)
    CheckOutTime = db.Column(db.Time, nullable=True)
    WorkingHours = db.Column(db.Float, nullable=True)
    OvertimeHours = db.Column(db.Float, nullable=True)
    OvertimeType = db.Column(db.String(20), nullable=True)  # <-- thêm mớ
    Status = db.Column(db.Unicode(50), nullable=True)
    Note = db.Column(db.Unicode(255), nullable=True)  # <-- thêm mới

    def __repr__(self):
        return f"<Attendance {self.EmployeeID} - {self.Date}>"

    # Thêm quan hệ đến HRProfile
    employee = db.relationship(
        "HRProfile",
        primaryjoin="Attendance.EmployeeID == foreign(HRProfile.EmployeeID)",
        lazy="joined",
        viewonly=True,
        uselist=False,  # ✅ THÊM DÒNG NÀY để chỉ nhận 1 đối tượng
    )
