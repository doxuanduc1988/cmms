from extensions import db


class HRDependent(db.Model):
    __tablename__ = "HRDependents"
    DependentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.String(20), db.ForeignKey("HRProfiles.EmployeeID"))
    FullName = db.Column(db.Unicode(100), nullable=False)
    Relationship = db.Column(db.Unicode(50))
    BirthDate = db.Column(db.Date)
    Gender = db.Column(db.String(10))
    Notes = db.Column(db.UnicodeText)

    profile = db.relationship("HRProfile", backref="dependent_list")
