from extensions import db


class Department(db.Model):
    __tablename__ = "Departments"
    __table_args__ = {"extend_existing": True}  # 👈 Thêm dòng này

    DepartmentCode = db.Column(db.Unicode(10), primary_key=True)
    DepartmentName = db.Column(db.Unicode(100), nullable=False)
    Description = db.Column(db.Unicode(100))
