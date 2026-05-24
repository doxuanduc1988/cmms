from extensions import db


class HREducationHistory(db.Model):
    __tablename__ = "HREducationHistory"

    EduID = db.Column(db.Integer, primary_key=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    Degree = db.Column(db.Unicode(100))  # Bằng cấp/chứng chỉ
    Major = db.Column(db.Unicode(100))  # Chuyên ngành
    Institution = db.Column(db.Unicode(255))  # Đơn vị đào tạo
    StartDate = db.Column(db.Date)
    EndDate = db.Column(db.Date)
    Form = db.Column(db.Unicode(100))  # Hình thức đào tạo (chính quy, tại chức, online…)
    Notes = db.Column(db.Unicode(255))
