from app import app
from extensions import db
from models.estimation import SkillGrade, WorkCategory

def seed_data():
    with app.app_context():
        db.create_all()
        # 1. Thêm Bậc tay nghề (Tham khảo thang 7 bậc ngành điện)
        # Lương ngày giả định: Lương cơ bản * Hệ số / 26
        grades = [
            SkillGrade(GradeCode="3/7", GradeName="Thợ bậc 3/7", Coefficient=2.31, DailyWage=350000, Description="Thợ bảo dưỡng cơ bản"),
            SkillGrade(GradeCode="3.5/7", GradeName="Thợ bậc 3.5/7", Coefficient=2.55, DailyWage=380000, Description="Thợ bảo dưỡng trung bình"),
            SkillGrade(GradeCode="4/7", GradeName="Thợ bậc 4/7", Coefficient=2.81, DailyWage=420000, Description="Thợ lành nghề"),
            SkillGrade(GradeCode="4.5/7", GradeName="Thợ bậc 4.5/7", Coefficient=3.10, DailyWage=460000, Description="Thợ lành nghề bậc cao"),
            SkillGrade(GradeCode="5/7", GradeName="Thợ bậc 5/7", Coefficient=3.41, DailyWage=510000, Description="Thợ bậc cao, tổ trưởng"),
            SkillGrade(GradeCode="6/7", GradeName="Thợ bậc 6/7", Coefficient=4.14, DailyWage=620000, Description="Chuyên gia kỹ thuật"),
            SkillGrade(GradeCode="7/7", GradeName="Thợ bậc 7/7", Coefficient=4.98, DailyWage=750000, Description="Bậc thợ cao nhất"),
        ]
        
        # 2. Thêm Đầu mục công việc mẫu
        categories = [
            WorkCategory(CategoryCode="BD-LH-01", CategoryName="Bảo dưỡng hệ thống ghi xích lò hơi", Unit="công", Description="Kiểm tra, bôi trơn, thay thế xích hỏng"),
            WorkCategory(CategoryCode="SC-BT-02", CategoryName="Sửa chữa bơm nước cấp", Unit="công", Description="Tháo lắp, thay phớt, căn chỉnh đồng tâm"),
            WorkCategory(CategoryCode="BD-MP-03", CategoryName="Bảo dưỡng máy phát điện", Unit="công", Description="Kiểm tra chổi than, vệ sinh cổ góp"),
            WorkCategory(CategoryCode="SC-VD-04", CategoryName="Sửa chữa van điều khiển hơi chính", Unit="công", Description="Rà van, thay bộ kit sửa chữa"),
            WorkCategory(CategoryCode="BD-QT-05", CategoryName="Bảo dưỡng quạt gió lò hơi", Unit="công", Description="Cân bằng động cánh quạt, thay vòng bi"),
        ]
        
        # Xóa dữ liệu cũ nếu muốn (tùy chọn)
        # SkillGrade.query.delete()
        # WorkCategory.query.delete()
        
        # Thêm mới
        for g in grades:
            if not SkillGrade.query.filter_by(GradeCode=g.GradeCode).first():
                db.session.add(g)
                
        for c in categories:
            if not WorkCategory.query.filter_by(CategoryCode=c.CategoryCode).first():
                db.session.add(c)
        
        db.session.commit()
        print("✅ Đã nạp dữ liệu mẫu cho module Dự toán thành công!")

if __name__ == "__main__":
    seed_data()
