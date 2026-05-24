from extensions import db


class HRHealthInfo(db.Model):
    __tablename__ = "HRHealthInfo"

    HealthID = db.Column(db.Integer, primary_key=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    CheckDate = db.Column(db.Date)
    Height = db.Column(db.Float)
    Weight = db.Column(db.Float)
    BloodType = db.Column(db.String(5))
    HealthStatus = db.Column(db.Unicode(255))
    MedicalConditions = db.Column(db.UnicodeText)  # Unicode
    DoctorNotes = db.Column(db.UnicodeText)  # Unicode
    AttachmentFile = db.Column(db.String(255))  # file path nếu có
