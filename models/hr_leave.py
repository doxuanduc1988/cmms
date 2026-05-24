# models/hr_leave.py
from extensions import db


class HRLeaveRequest(db.Model):
    __tablename__ = "HRLeaveRequests"

    LeaveID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Unicode(20), nullable=False)
    LeaveType = db.Column(db.Unicode(50), nullable=False)  # 'Nghỉ phép' hoặc 'Nghỉ bù'
    StartDate = db.Column(db.Date, nullable=False)
    EndDate = db.Column(db.Date, nullable=False)
    TotalDays = db.Column(db.Float, nullable=False)
    OTReference = db.Column(db.Float, nullable=True)  # Giờ OT dùng để nghỉ bù
    Reason = db.Column(db.Unicode(255))
    Status = db.Column(db.Unicode(50), default="Chưa duyệt")
    Notes = db.Column(db.Text)

    def __repr__(self):
        return f"<HRLeaveRequest {self.LeaveType} {self.StartDate} - {self.EndDate}>"
