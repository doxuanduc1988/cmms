from extensions import db


# Bảng lịch sử lương
class SalaryHistory(db.Model):
    __tablename__ = "SalaryHistory"

    SalaryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Unicode(20), db.ForeignKey("Employees.EmployeeID"), nullable=False)
    SalaryAmount = db.Column(db.Float, nullable=False)
    EffectiveDate = db.Column(db.Date, nullable=False)
    Notes = db.Column(db.UnicodeText)

    employee = db.relationship("Employee", backref="salary_history")


# Bảng lịch sử đào tạo
class TrainingHistory(db.Model):
    __tablename__ = "TrainingHistory"

    TrainingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Unicode(20), db.ForeignKey("Employees.EmployeeID"), nullable=False)
    CourseName = db.Column(db.Unicode(255), nullable=False)
    TrainingInstitution = db.Column(db.Unicode(255))
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)
    Result = db.Column(db.Unicode(100))
    Notes = db.Column(db.UnicodeText)

    employee = db.relationship("Employee", backref="training_history")


# Bảng quy hoạch thăng tiến
class PromotionPlanning(db.Model):
    __tablename__ = "PromotionPlanning"

    PlanningID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.Unicode(20), db.ForeignKey("Employees.EmployeeID"), nullable=False)
    TargetPosition = db.Column(db.Unicode(100), nullable=False)
    PlanningYear = db.Column(db.Integer, nullable=False)
    Notes = db.Column(db.UnicodeText)

    employee = db.relationship("Employee", backref="promotion_planning")
