from app import app
from extensions import db
from sqlalchemy import text

def try_create():
    with app.app_context():
        try:
            db.session.execute(text("""
                CREATE TABLE [SkillGrades] (
                    [GradeID] INTEGER NOT NULL IDENTITY, 
                    [GradeCode] NVARCHAR(20) NOT NULL, 
                    [GradeName] NVARCHAR(100) NOT NULL, 
                    [Coefficient] FLOAT NOT NULL, 
                    [DailyWage] FLOAT NOT NULL, 
                    [Description] NVARCHAR(255) NULL, 
                    PRIMARY KEY ([GradeID]), 
                    UNIQUE ([GradeCode])
                )
            """))
            db.session.commit()
            print("✅ Created SkillGrades via raw SQL")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    try_create()
