from extensions import db
from models import AuditLog
from datetime import datetime


def log_action(employee_id, action, module, description=None):
    log = AuditLog(
        EmployeeID=employee_id, Action=action, Module=module, Description=description, Timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
