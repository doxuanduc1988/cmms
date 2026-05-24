from extensions import db
from datetime import datetime


class SkillGrade(db.Model):
    """Bậc tay nghề công nhân (thang 7 bậc theo quy định ngành điện VN)."""

    __tablename__ = "SkillGrades"

    GradeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    GradeCode = db.Column(db.Unicode(20), unique=True, nullable=False)  # VD: "3.5/7", "4/7"
    GradeName = db.Column(db.Unicode(100), nullable=False)  # VD: "Bậc 3.5/7"
    Coefficient = db.Column(db.Float, nullable=False)  # Hệ số lương
    DailyWage = db.Column(db.Float, nullable=False)  # Lương ngày (VNĐ)
    Description = db.Column(db.Unicode(255))


class WorkCategory(db.Model):
    """Đầu mục công việc bảo dưỡng / sửa chữa."""

    __tablename__ = "WorkCategories"

    CategoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CategoryCode = db.Column(db.Unicode(20), unique=True, nullable=False)
    CategoryName = db.Column(db.Unicode(200), nullable=False)
    Unit = db.Column(db.Unicode(50), default="công")  # đơn vị tính
    Description = db.Column(db.Unicode(500))


class EstimationSheet(db.Model):
    """Phiếu dự toán chi phí nhân công."""

    __tablename__ = "EstimationSheets"

    SheetID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SheetCode = db.Column(db.Unicode(50), unique=True, nullable=False)
    SheetName = db.Column(db.Unicode(200), nullable=False)
    ProjectName = db.Column(db.Unicode(300))  # Tên công trình / hạng mục sửa chữa
    CreatedBy = db.Column(db.Unicode(100))
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.Unicode(30), default="Draft")  # Draft / Submitted / Approved
    TotalCost = db.Column(db.Float, default=0)
    Notes = db.Column(db.UnicodeText)

    items = db.relationship("EstimationItem", backref="sheet", lazy=True, cascade="all, delete-orphan")


class EstimationItem(db.Model):
    """Dòng chi tiết trong phiếu dự toán."""

    __tablename__ = "EstimationItems"

    ItemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SheetID = db.Column(db.Integer, db.ForeignKey("EstimationSheets.SheetID"), nullable=False)
    CategoryID = db.Column(db.Integer, db.ForeignKey("WorkCategories.CategoryID"), nullable=False)
    GradeID = db.Column(db.Integer, db.ForeignKey("SkillGrades.GradeID"), nullable=False)
    WorkDays = db.Column(db.Float, nullable=False, default=1)  # Số công (ngày)
    NumberOfWorkers = db.Column(db.Integer, nullable=False, default=1)  # Số lượng nhân công
    UnitPrice = db.Column(db.Float, default=0)  # Đơn giá = DailyWage * Coefficient
    TotalPrice = db.Column(db.Float, default=0)  # = UnitPrice * WorkDays * NumberOfWorkers
    Note = db.Column(db.Unicode(500))

    category = db.relationship("WorkCategory", lazy="joined")
    grade = db.relationship("SkillGrade", lazy="joined")
