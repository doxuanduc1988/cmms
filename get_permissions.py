from app import app, db
from models.modules import Module
from models.permissions import Permission

with app.app_context():
    permissions = Permission.query.all()
    print("\n--- PERMISSIONS ---")
    for p in permissions:
        m_code = p.module.ModuleCode if p.module else 'None'
        print(f"[{p.PermissionID}] {m_code} - Action: {p.Action} - Description: {p.Description}")
