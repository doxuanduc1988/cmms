from app import app, db
from sqlalchemy import text

def check_columns():
    with app.app_context():
        try:
            # Check HRProfiles columns
            result = db.session.execute(text("SELECT TOP 1 * FROM HRProfiles")) # For MSSQL
            print("Columns in HRProfiles:", result.keys())
        except Exception as e:
            try:
                result = db.session.execute(text("SELECT * FROM HRProfiles LIMIT 1")) # For MySQL/MariaDB
                print("Columns in HRProfiles:", result.keys())
            except Exception as e2:
                print("Error checking columns:", e2)

if __name__ == "__main__":
    check_columns()
