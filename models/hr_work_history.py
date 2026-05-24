# models/hr_work_history.py
from extensions import db


class HRWorkHistory(db.Model):
    __tablename__ = "HRWorkHistory"

    WorkID = db.Column(db.Integer, primary_key=True)
    EmployeeID = db.Column(db.Unicode(20), db.ForeignKey("HRProfiles.EmployeeID"), nullable=False)
    StartDate = db.Column(db.Date, nullable=False)
    ToDate = db.Column(db.Date)
    DepartmentName = db.Column(db.Unicode(255))
    Position = db.Column(db.Unicode(100))
    Notes = db.Column(db.Unicode)

    # Quan hệ nếu cần truy ngược
    # employee = db.relationship('HRProfile', backref='work_history', lazy=True)
    # department = db.relationship('Department', backref='work_history', lazy=True)
