# models/shift_definition.py
from extensions import db


class ShiftDefinition(db.Model):
    __tablename__ = "ShiftDefinitions"

    ShiftID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ShiftCode = db.Column(db.String(20), nullable=False)
    ShiftName = db.Column(db.Unicode(50), nullable=False)
    StartTime = db.Column(db.Time, nullable=False)
    EndTime = db.Column(db.Time, nullable=False)
    Description = db.Column(db.Unicode(255))

    def __repr__(self):
        return f"<ShiftDefinition {self.ShiftName}>"
