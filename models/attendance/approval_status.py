from extensions import db
from datetime import datetime


class AttendanceApprovalStatus(db.Model):
    __tablename__ = "AttendanceApprovalStatus"

    AttendanceID = db.Column(db.Integer, db.ForeignKey("Attendance.AttendanceID"), primary_key=True)

    Status = db.Column(db.String(20))  # Pending, Approved, Rejected, Finalized
    LastLevel = db.Column(db.Integer)  # 1, 2, 3
    LastAction = db.Column(db.String(20))  # Approved, Rejected
    LastModifiedAt = db.Column(db.DateTime)
    LastModifiedBy = db.Column(db.String(20))
