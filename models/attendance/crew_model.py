# models/crew_definition.py
from extensions import db


class CrewDefinition(db.Model):
    __tablename__ = "CrewDefinitions"

    CrewID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CrewCode = db.Column(db.String(20), nullable=False)
    CrewName = db.Column(db.Unicode(50), nullable=False)
    Description = db.Column(db.Unicode(255))

    def __repr__(self):
        return f"<CrewDefinition {self.CrewCode} - {self.CrewName}>"
