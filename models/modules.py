from extensions import db


class Module(db.Model):
    __tablename__ = "Modules"

    ModuleID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ModuleCode = db.Column(db.Unicode(50), nullable=False, unique=True)
    ModuleName = db.Column(db.Unicode(100), nullable=False)
    Description = db.Column(db.Unicode(255))
