from extensions import db
from datetime import datetime


class AttendanceApprovalFlow(db.Model):
    __tablename__ = "AttendanceApprovalFlow"

    ApprovalID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    AttendanceID = db.Column(db.Integer, nullable=False)
    ApprovalLevel = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    Action = db.Column(db.String(20), nullable=False)  # Approved, Rejected
    ApprovedBy = db.Column(db.String(20), nullable=False)
    ApprovedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Note = db.Column(db.Unicode(255))
