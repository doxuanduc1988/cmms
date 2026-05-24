from extensions import db


class HRSalaryHistory(db.Model):
    __tablename__ = "HRSalaryHistory"

    SalaryID = db.Column(db.Integer, primary_key=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    EffectiveDate = db.Column(db.Date, nullable=False)
    SalaryCode = db.Column(db.String(50))  # Mã bậc
    Description = db.Column(db.Unicode(100))  # Mô tả chức danh
    Reason = db.Column(db.Unicode(255))
    Notes = db.Column(db.Unicode(255))
    Coefficient = db.Column(db.Numeric(5, 2))  # hoặc DECIMAL phù hợp với SQL Server
