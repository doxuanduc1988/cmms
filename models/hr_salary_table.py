from extensions import db


class HRSalaryTable(db.Model):
    __tablename__ = "HRSalaryTable"

    SalaryCode = db.Column(db.String(20), primary_key=True)
    Description = db.Column(db.Unicode(100))
    Coefficient = db.Column(db.Numeric(5, 2))
