from extensions import db


class HRAwardsDiscipline(db.Model):
    __tablename__ = "HRAwardsDiscipline"

    RecordID = db.Column(db.Integer, primary_key=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    Type = db.Column(db.Unicode(50))  # 'Khen thưởng' hoặc 'Kỷ luật'
    Title = db.Column(db.Unicode(255))
    Date = db.Column(db.Date)
    DecisionNumber = db.Column(db.Unicode(100))
    Notes = db.Column(db.Unicode(255))
