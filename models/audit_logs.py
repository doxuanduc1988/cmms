from extensions import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = "AuditLogs"

    AuditID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    Action = db.Column(db.Unicode(50), nullable=False)
    Module = db.Column(db.Unicode(50), nullable=False)
    Description = db.Column(db.Unicode(255))
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)
