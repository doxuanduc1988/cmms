from app import app, db
from models.modules import Module
with app.app_context():
    for m in Module.query.all():
        print(f"[{m.ModuleID}] {m.ModuleCode}: {m.ModuleName}")
