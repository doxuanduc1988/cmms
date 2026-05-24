from flask import Blueprint, render_template, request, redirect, url_for, flash
from decimal import Decimal
from extensions import db
from models.hr_salary_history import HRSalaryHistory
from models.hr.hr_profiles import HRProfile
from utils.permission_utils import check_permission
from models.hr_salary_table import HRSalaryTable  # 👈 đảm bảo import đúng model

salary_history_bp = Blueprint("salary_history", __name__, url_prefix="/hr")


@salary_history_bp.route("/<employee_id>/salary-history")
@check_permission("hr", "read")
def salary_history_list(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    history = (
        HRSalaryHistory.query.filter_by(EmployeeID=employee_id).order_by(HRSalaryHistory.EffectiveDate.desc()).all()
    )
    return render_template("hr/salary_history_list.html", employee=employee, history=history)


@salary_history_bp.route("/<employee_id>/salary-history/create", methods=["GET", "POST"])
@check_permission("hr", "create")
def salary_history_create(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)

    if request.method == "POST":
        salary_code = (request.form.get("SalaryCode") or "").strip()
        st = HRSalaryTable.query.filter_by(SalaryCode=salary_code).first()
        if not st:
            flash("Mã bậc lương không tồn tại.", "danger")
            return redirect(url_for("salary_history.salary_history_create", employee_id=employee_id))

        # Ép kiểu an toàn từ DB; KHÔNG lấy từ form
        try:
            coefficient = Decimal(str(st.Coefficient)) if st.Coefficient is not None else None
        except Exception:
            flash("Hệ số lương không hợp lệ trong bảng bậc lương.", "danger")
            return redirect(url_for("salary_history.salary_history_create", employee_id=employee_id))

        rec = HRSalaryHistory(
            EmployeeID=employee_id,
            EffectiveDate=(request.form.get("EffectiveDate") or "").strip(),
            SalaryCode=salary_code,
            Description=(st.Description or "").strip(),
            Reason=(request.form.get("Reason") or "").strip(),
            Notes=(request.form.get("Notes") or "").strip(),
            Coefficient=coefficient,
        )
        db.session.add(rec)
        db.session.commit()
        flash("Đã thêm quá trình lương.", "success")
        return redirect(url_for("salary_history.salary_history_list", employee_id=employee_id))

    # NHÁNH GET: render form + danh sách bậc lương
    salary_table = HRSalaryTable.query.order_by(HRSalaryTable.SalaryCode.asc()).all()
    return render_template("hr/salary_history_form.html", employee=employee, action="create", salary_table=salary_table)


@salary_history_bp.route("/<employee_id>/salary-history/<int:salary_id>/edit", methods=["GET", "POST"])
@check_permission("hr", "update")
def salary_history_edit(employee_id, salary_id):
    employee = HRProfile.query.get_or_404(employee_id)
    record = HRSalaryHistory.query.get_or_404(salary_id)

    if request.method == "POST":
        record.EffectiveDate = (request.form.get("EffectiveDate") or "").strip()
        new_code = (request.form.get("SalaryCode") or "").strip()
        st = HRSalaryTable.query.filter_by(SalaryCode=new_code).first()
        if not st:
            flash("Mã bậc lương không tồn tại.", "danger")
            return redirect(url_for("salary_history.salary_history_edit", employee_id=employee_id, salary_id=salary_id))
        try:
            record.Coefficient = Decimal(str(st.Coefficient)) if st.Coefficient is not None else None
        except Exception:
            flash("Hệ số lương không hợp lệ trong bảng bậc lương.", "danger")
            return redirect(url_for("salary_history.salary_history_edit", employee_id=employee_id, salary_id=salary_id))

        record.SalaryCode = new_code
        record.Description = (st.Description or "").strip()
        record.Reason = (request.form.get("Reason") or "").strip()
        record.Notes = (request.form.get("Notes") or "").strip()

        db.session.commit()
        flash("Đã cập nhật quá trình lương.", "success")
        return redirect(url_for("salary_history.salary_history_list", employee_id=employee_id))

    # NHÁNH GET: render form edit
    salary_table = HRSalaryTable.query.order_by(HRSalaryTable.SalaryCode.asc()).all()
    return render_template(
        "hr/salary_history_form.html", employee=employee, record=record, action="edit", salary_table=salary_table
    )


@salary_history_bp.route("/<employee_id>/salary-history/<int:salary_id>/delete", methods=["POST"])
@check_permission("hr", "delete")
def salary_history_delete(employee_id, salary_id):
    record = HRSalaryHistory.query.get_or_404(salary_id)
    db.session.delete(record)
    db.session.commit()
    flash("Đã xoá bản ghi.", "info")
    return redirect(url_for("salary_history.salary_history_list", employee_id=employee_id))
