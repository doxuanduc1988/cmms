# models/procurement/tender_package_model.py
from extensions import db
from sqlalchemy.dialects.mssql import NVARCHAR, DECIMAL


class TenderPackage(db.Model):
    __tablename__ = "TenderPackages"

    PackageCode = db.Column(NVARCHAR(100), primary_key=True)  # trước đây hay bị String(...)
    PackageName = db.Column(NVARCHAR(1000), nullable=False)  # nới lên 1000 cho đủ dữ liệu
    PackageType = db.Column(NVARCHAR(200), nullable=True)
    PlanValue = db.Column(DECIMAL(18, 2), nullable=True)
