from extensions import db


class HRContract(db.Model):
    __tablename__ = "HRContracts"

    ContractID = db.Column(db.Integer, primary_key=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    ContractNumber = db.Column(db.Unicode(50))
    ContractType = db.Column(db.Unicode(100))
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)
    SalaryCode = db.Column(db.Unicode(20), nullable=False)
    Status = db.Column(db.Unicode(50), nullable=False)
    FileAttachment = db.Column(db.String(255))
    Description = db.Column(db.Text)

    def __repr__(self):
        return f"<HRContract {self.ContractNumber}>"
