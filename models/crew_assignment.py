# models/crew_assignment.py
from extensions import db


class CrewAssignment(db.Model):
    __tablename__ = "CrewAssignments"

    AssignmentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeID = db.Column(db.String(20), nullable=False)
    CrewID = db.Column(db.Integer, nullable=False)
    DepartmentCode = db.Column(db.String(10), db.ForeignKey("Departments.DepartmentCode"), nullable=False)
    JobPositionID = db.Column(db.Integer, db.ForeignKey("JobPositions.JobPositionID"), nullable=True)
    StartDate = db.Column(db.Date, nullable=False)
    EndDate = db.Column(db.Date)

    # Relationships
    department = db.relationship("Department", backref="crew_assignments", lazy=True)
    job_position = db.relationship("JobPosition", backref="crew_assignments", lazy=True)

    def __repr__(self):
        return f"<CrewAssignment EmployeeID={self.EmployeeID} CrewID={self.CrewID}>"
