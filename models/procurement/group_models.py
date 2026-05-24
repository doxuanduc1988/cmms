from extensions import db


class TenderExpertMember(db.Model):
    """Thành viên Tổ chuyên gia theo từng gói thầu."""

    __tablename__ = "TenderExpertMembers"

    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PackageCode = db.Column(db.String(50), nullable=False, index=True)
    EmployeeID = db.Column(db.String(50), nullable=False, index=True)


class TenderAppraisalMember(db.Model):
    """Thành viên Tổ thẩm định theo từng gói thầu."""

    __tablename__ = "TenderAppraisalMembers"

    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PackageCode = db.Column(db.String(50), nullable=False, index=True)
    EmployeeID = db.Column(db.String(50), nullable=False, index=True)
