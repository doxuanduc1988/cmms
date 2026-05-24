# models/hr_contracts.py
from app import db


class HRContract(db.Model):
    __tablename__ = "HRContracts"

    ContractID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    ContractNumber = db.Column(db.String(50), nullable=False)
    ContractType = db.Column(db.String(100), nullable=False)
    StartDate = db.Column(db.Date, nullable=False)
    EndDate = db.Column(db.Date, nullable=True)
    SalaryCode = db.Column(db.String(20), nullable=False)
    Status = db.Column(db.String(50), nullable=False)
    FileAttachment = db.Column(db.String(255))
    Description = db.Column(db.Text)

    def __repr__(self):
        return f"<HRContract {self.ContractNumber}>"
