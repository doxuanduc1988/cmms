from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from extensions import db
from utils.permission_utils import check_permission

from models.estimation import SkillGrade, WorkCategory, EstimationSheet, EstimationItem
from datetime import datetime
import io
import pandas as pd
from flask import send_file

estimation_bp = Blueprint("estimation", __name__, url_prefix="/estimation")


# =============================================================================
# DASHBOARD DỰ TOÁN
# =============================================================================


@estimation_bp.route("/")
@login_required
@check_permission("estimation", "read")
def estimation_dashboard():
    return render_template("estimation/dashboard.html")


# =============================================================================
# QUẢN LÝ BẬC TAY NGHỀ (SKILL GRADES)
# =============================================================================


@estimation_bp.route("/grades")
@login_required
@check_permission("estimation", "read")
def list_grades():
    grades = SkillGrade.query.order_by(SkillGrade.Coefficient).all()
    return render_template("estimation/grades_list.html", grades=grades)


@estimation_bp.route("/grades/create", methods=["GET", "POST"])
@login_required
@check_permission("estimation", "create")
def create_grade():
    if request.method == "POST":
        grade = SkillGrade(
            GradeCode=request.form["GradeCode"],
            GradeName=request.form["GradeName"],
            Coefficient=float(request.form["Coefficient"]),
            DailyWage=float(request.form["DailyWage"]),
            Description=request.form.get("Description", ""),
        )
        db.session.add(grade)
        db.session.commit()
        flash("✅ Đã thêm bậc tay nghề!", "success")
        return redirect(url_for("estimation.list_grades"))
    return render_template("estimation/grades_form.html", grade=None)


@estimation_bp.route("/grades/edit/<int:grade_id>", methods=["GET", "POST"])
@login_required
@check_permission("estimation", "update")
def edit_grade(grade_id):
    grade = SkillGrade.query.get_or_404(grade_id)
    if request.method == "POST":
        grade.GradeCode = request.form["GradeCode"]
        grade.GradeName = request.form["GradeName"]
        grade.Coefficient = float(request.form["Coefficient"])
        grade.DailyWage = float(request.form["DailyWage"])
        grade.Description = request.form.get("Description", "")
        db.session.commit()
        flash("✅ Đã cập nhật!", "success")
        return redirect(url_for("estimation.list_grades"))
    return render_template("estimation/grades_form.html", grade=grade)


@estimation_bp.route("/grades/delete/<int:grade_id>", methods=["POST"])
@login_required
@check_permission("estimation", "delete")
def delete_grade(grade_id):
    grade = SkillGrade.query.get_or_404(grade_id)
    db.session.delete(grade)
    db.session.commit()
    flash("✅ Đã xoá bậc tay nghề!", "success")
    return redirect(url_for("estimation.list_grades"))


# =============================================================================
# QUẢN LÝ ĐẦU MỤC CÔNG VIỆC (WORK CATEGORIES)
# =============================================================================


@estimation_bp.route("/categories")
@login_required
@check_permission("estimation", "read")
def list_categories():
    categories = WorkCategory.query.order_by(WorkCategory.CategoryCode).all()
    return render_template("estimation/categories_list.html", categories=categories)


@estimation_bp.route("/categories/create", methods=["GET", "POST"])
@login_required
@check_permission("estimation", "create")
def create_category():
    if request.method == "POST":
        cat = WorkCategory(
            CategoryCode=request.form["CategoryCode"],
            CategoryName=request.form["CategoryName"],
            Unit=request.form.get("Unit", "công"),
            Description=request.form.get("Description", ""),
        )
        db.session.add(cat)
        db.session.commit()
        flash("✅ Đã thêm đầu mục công việc!", "success")
        return redirect(url_for("estimation.list_categories"))
    return render_template("estimation/categories_form.html", category=None)


@estimation_bp.route("/categories/edit/<int:cat_id>", methods=["GET", "POST"])
@login_required
@check_permission("estimation", "update")
def edit_category(cat_id):
    cat = WorkCategory.query.get_or_404(cat_id)
    if request.method == "POST":
        cat.CategoryCode = request.form["CategoryCode"]
        cat.CategoryName = request.form["CategoryName"]
        cat.Unit = request.form.get("Unit", "công")
        cat.Description = request.form.get("Description", "")
        db.session.commit()
        flash("✅ Đã cập nhật!", "success")
        return redirect(url_for("estimation.list_categories"))
    return render_template("estimation/categories_form.html", category=cat)


@estimation_bp.route("/categories/delete/<int:cat_id>", methods=["POST"])
@login_required
@check_permission("estimation", "delete")
def delete_category(cat_id):
    cat = WorkCategory.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash("✅ Đã xoá đầu mục công việc!", "success")
    return redirect(url_for("estimation.list_categories"))


# =============================================================================
# QUẢN LÝ PHIẾU DỰ TOÁN (ESTIMATION SHEETS)
# =============================================================================


@estimation_bp.route("/sheets")
@login_required
@check_permission("estimation", "read")
def list_sheets():
    sheets = EstimationSheet.query.order_by(EstimationSheet.CreatedAt.desc()).all()
    return render_template("estimation/sheets_list.html", sheets=sheets)


@estimation_bp.route("/sheets/create", methods=["GET", "POST"])
@login_required
@check_permission("estimation", "create")
def create_sheet():
    if request.method == "POST":
        created_at_str = request.form.get("CreatedAt")
        created_at = datetime.strptime(created_at_str, "%Y-%m-%d") if created_at_str else datetime.utcnow()
        
        sheet = EstimationSheet(
            SheetCode=request.form["SheetCode"],
            SheetName=request.form["SheetName"],
            ProjectName=request.form.get("ProjectName", ""),
            CreatedBy=session.get("full_name", session.get("username", "unknown")),
            CreatedAt=created_at,
            Status=request.form.get("Status", "Draft"),
            Notes=request.form.get("Notes", ""),
        )
        db.session.add(sheet)
        db.session.commit()
        flash("✅ Đã tạo phiếu dự toán!", "success")
        return redirect(url_for("estimation.edit_sheet", sheet_id=sheet.SheetID))
    now_date = datetime.utcnow().strftime("%Y-%m-%d")
    return render_template("estimation/sheets_form.html", sheet=None, now_date=now_date)


@estimation_bp.route("/sheets/<int:sheet_id>", methods=["GET", "POST"])
@login_required
@check_permission("estimation", "update")
def edit_sheet(sheet_id):
    sheet = EstimationSheet.query.get_or_404(sheet_id)
    categories = WorkCategory.query.order_by(WorkCategory.CategoryCode).all()
    grades = SkillGrade.query.order_by(SkillGrade.Coefficient).all()

    if request.method == "POST":
        sheet.SheetCode = request.form["SheetCode"]
        sheet.SheetName = request.form["SheetName"]
        sheet.ProjectName = request.form.get("ProjectName", "")
        
        created_at_str = request.form.get("CreatedAt")
        if created_at_str:
            sheet.CreatedAt = datetime.strptime(created_at_str, "%Y-%m-%d")
            
        sheet.Status = request.form.get("Status", "Draft")
        sheet.Notes = request.form.get("Notes", "")
        db.session.commit()
        flash("✅ Đã cập nhật phiếu dự toán!", "success")
        return redirect(url_for("estimation.edit_sheet", sheet_id=sheet.SheetID))

    # Tính tổng chi phí
    total = sum(item.TotalPrice or 0 for item in sheet.items)
    sheet.TotalCost = total
    db.session.commit()

    return render_template(
        "estimation/sheets_detail.html",
        sheet=sheet,
        categories=categories,
        grades=grades,
    )


@estimation_bp.route("/sheets/<int:sheet_id>/delete", methods=["POST"])
@login_required
@check_permission("estimation", "delete")
def delete_sheet(sheet_id):
    sheet = EstimationSheet.query.get_or_404(sheet_id)
    db.session.delete(sheet)
    db.session.commit()
    flash("✅ Đã xoá phiếu dự toán!", "success")
    return redirect(url_for("estimation.list_sheets"))


# =============================================================================
# QUẢN LÝ DÒNG CHI TIẾT DỰ TOÁN (ESTIMATION ITEMS)
# =============================================================================


@estimation_bp.route("/sheets/<int:sheet_id>/items/add", methods=["POST"])
@login_required
def add_item(sheet_id):
    sheet = EstimationSheet.query.get_or_404(sheet_id)
    grade = SkillGrade.query.get(int(request.form["GradeID"]))

    work_days = float(request.form.get("WorkDays", 1))
    num_workers = int(request.form.get("NumberOfWorkers", 1))
    unit_price = grade.DailyWage * grade.Coefficient if grade else 0
    total_price = unit_price * work_days * num_workers

    item = EstimationItem(
        SheetID=sheet_id,
        CategoryID=int(request.form["CategoryID"]),
        GradeID=int(request.form["GradeID"]),
        WorkDays=work_days,
        NumberOfWorkers=num_workers,
        UnitPrice=unit_price,
        TotalPrice=total_price,
        Note=request.form.get("Note", ""),
    )
    db.session.add(item)

    # Cập nhật tổng
    sheet.TotalCost = (sheet.TotalCost or 0) + total_price
    db.session.commit()
    flash("✅ Đã thêm dòng dự toán!", "success")
    return redirect(url_for("estimation.edit_sheet", sheet_id=sheet_id))


@estimation_bp.route("/items/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    item = EstimationItem.query.get_or_404(item_id)
    sheet_id = item.SheetID
    db.session.delete(item)
    db.session.commit()

    # Recalc total
    sheet = EstimationSheet.query.get(sheet_id)
    sheet.TotalCost = sum(i.TotalPrice or 0 for i in sheet.items)
    db.session.commit()

    flash("✅ Đã xoá dòng!", "success")
    return redirect(url_for("estimation.edit_sheet", sheet_id=sheet_id))


# =============================================================================
# API - Lấy đơn giá theo bậc tay nghề (dùng cho AJAX tính giá tự động)
# =============================================================================


@estimation_bp.route("/api/grade/<int:grade_id>")
@login_required
def get_grade_info(grade_id):
    grade = SkillGrade.query.get_or_404(grade_id)
    return jsonify(
        {
            "GradeID": grade.GradeID,
            "GradeCode": grade.GradeCode,
            "Coefficient": grade.Coefficient,
            "DailyWage": grade.DailyWage,
            "UnitPrice": grade.DailyWage * grade.Coefficient,
        }
    )


# =============================================================================
# XUẤT EXCEL DỰ TOÁN
# =============================================================================


@estimation_bp.route("/sheets/<int:sheet_id>/export")
@login_required
def export_sheet_excel(sheet_id):
    sheet = EstimationSheet.query.get_or_404(sheet_id)
    items = EstimationItem.query.filter_by(SheetID=sheet_id).all()

    data = []
    for idx, item in enumerate(items, 1):
        data.append(
            {
                "STT": idx,
                "Đầu mục công việc": item.category.CategoryName if item.category else "",
                "Bậc thợ": item.grade.GradeCode if item.grade else "",
                "Hệ số": item.grade.Coefficient if item.grade else 0,
                "Lương ngày (VNĐ)": item.grade.DailyWage if item.grade else 0,
                "Đơn giá (VNĐ)": item.UnitPrice or 0,
                "Số công": item.WorkDays,
                "Số nhân công": item.NumberOfWorkers,
                "Thành tiền (VNĐ)": item.TotalPrice or 0,
                "Ghi chú": item.Note or "",
            }
        )

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dự toán")
    output.seek(0)

    filename = f"DuToan_{sheet.SheetCode}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
