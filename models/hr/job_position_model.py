# models/hr/job_position_model.py

from extensions import db


class JobPosition(db.Model):
    __tablename__ = "JobPositions"

    JobPositionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    JobPositionCode = db.Column(db.String(20), nullable=False)
    JobPositionName = db.Column(db.Unicode(100), nullable=False)
    Description = db.Column(db.Unicode(255))

    def __repr__(self):
        return f"<JobPosition {self.JobPositionCode} - {self.JobPositionName}>"
