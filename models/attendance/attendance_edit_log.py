from extensions import db
from datetime import datetime


class AttendanceEditLog(db.Model):
    __tablename__ = "AttendanceEditLog"

    LogID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    AttendanceID = db.Column(db.Integer, nullable=False)
    EmployeeID = db.Column(db.String(20))  # Người được chấm công
    EditedBy = db.Column(db.Unicode(50))  # Người thực hiện chỉnh sửa
    EditedAt = db.Column(db.DateTime, default=datetime.utcnow)

    OldCheckIn = db.Column(db.String(10))
    OldCheckOut = db.Column(db.String(10))
    OldStatus = db.Column(db.String(20))
    OldNote = db.Column(db.Unicode(255))

    NewCheckIn = db.Column(db.String(10))
    NewCheckOut = db.Column(db.String(10))
    NewStatus = db.Column(db.String(20))
    NewNote = db.Column(db.Unicode(255))

    ChangeType = db.Column(db.String(20))  # Ví dụ: 'Manual Edit', 'Auto OT Split', 'Rejected Revision'
    FieldChanged = db.Column(db.Unicode(100))  # Một tên trường hoặc 'Multiple'

    EditorRole = db.Column(db.Unicode(50))  # 'Trưởng phòng', 'Hành chính', 'Nhân sự',...
    Source = db.Column(db.Unicode(50))  # 'Web UI', 'API', 'System Auto', 'Rejected Fix'
