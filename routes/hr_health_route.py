from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.hr_health_info import HRHealthInfo
from extensions import db
from utils.upload_file import save_uploaded_file, delete_file_if_exists
from config import UPLOAD_SUBFOLDER_HEALTH

# from decorators import check_permission  # nếu cần import
from utils.permission_utils import check_permission

hr_health_bp = Blueprint("hr_health", __name__, url_prefix="/hr/<employee_id>/health")


@hr_health_bp.route("/", methods=["GET", "POST"])
@check_permission("hr", "create")
def list_health(employee_id):
    if request.method == "POST":
        try:
            file = request.files.get("AttachmentFile")
            filename = save_uploaded_file(file, UPLOAD_SUBFOLDER_HEALTH, prefix=employee_id)

            new_record = HRHealthInfo(
                EmployeeID=employee_id,
                CheckDate=request.form.get("CheckDate"),
                Height=request.form.get("Height"),
                Weight=request.form.get("Weight"),
                BloodType=request.form.get("BloodType"),
                HealthStatus=request.form.get("HealthStatus"),
                MedicalConditions=request.form.get("MedicalConditions"),
                DoctorNotes=request.form.get("DoctorNotes"),
                AttachmentFile=filename,
            )
            db.session.add(new_record)
            db.session.commit()
            flash("Đã thêm thông tin sức khỏe", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "danger")
        return redirect(url_for("hr_health.list_health", employee_id=employee_id))

    records = HRHealthInfo.query.filter_by(EmployeeID=employee_id).order_by(HRHealthInfo.CheckDate.desc()).all()
    return render_template("hr/health/list.html", records=records, employee_id=employee_id, mode="add", record=None)


@hr_health_bp.route("/edit/<int:health_id>", methods=["GET", "POST"])
@check_permission("hr", "update")
def edit_health(employee_id, health_id):
    record = HRHealthInfo.query.get_or_404(health_id)
    if request.method == "POST":
        try:
            file = request.files.get("AttachmentFile")
            if file and file.filename:
                # Xoá file cũ nếu có
                delete_file_if_exists(UPLOAD_SUBFOLDER_HEALTH, record.AttachmentFile)
                filename = save_uploaded_file(file, UPLOAD_SUBFOLDER_HEALTH, prefix=employee_id)
                record.AttachmentFile = filename

            record.CheckDate = request.form.get("CheckDate")
            record.Height = request.form.get("Height")
            record.Weight = request.form.get("Weight")
            record.BloodType = request.form.get("BloodType")
            record.HealthStatus = request.form.get("HealthStatus")
            record.MedicalConditions = request.form.get("MedicalConditions")
            record.DoctorNotes = request.form.get("DoctorNotes")

            db.session.commit()
            flash("Đã cập nhật thông tin sức khỏe", "success")
            return redirect(url_for("hr_health.list_health", employee_id=employee_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "danger")

    records = HRHealthInfo.query.filter_by(EmployeeID=employee_id).order_by(HRHealthInfo.CheckDate.desc()).all()
    return render_template("hr/health/list.html", records=records, employee_id=employee_id, mode="edit", record=record)


@hr_health_bp.route("/delete/<int:health_id>", methods=["POST"])
@check_permission("hr", "delete")
def delete_health(employee_id, health_id):
    record = HRHealthInfo.query.get(health_id)
    if record:
        # Xoá file đính kèm nếu có
        delete_file_if_exists(UPLOAD_SUBFOLDER_HEALTH, record.AttachmentFile)

        db.session.delete(record)
        db.session.commit()
        flash("Đã xoá thông tin sức khỏe", "success")
    else:
        flash("Không tìm thấy dữ liệu", "danger")
    return redirect(url_for("hr_health.list_health", employee_id=employee_id))


@hr_health_bp.route("/search", methods=["GET"])
@check_permission("hr", "read")
def search_health():
    query = request.args.get("query", "").strip()
    from models.hr_profiles import HRProfile
    from models.job_positions import JobPosition  # nếu cần

    profiles = []
    if query:
        profiles = (
            HRProfile.query.outerjoin(JobPosition, HRProfile.JobPositionID == JobPosition.JobPositionID)
            .filter((HRProfile.EmployeeID.ilike(f"%{query}%")) | (HRProfile.FullName.ilike(f"%{query}%")))
            .order_by(HRProfile.FullName)
            .all()
        )

    return render_template("health/index.html", profiles=profiles)
