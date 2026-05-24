from flask import Blueprint, request, redirect, url_for, flash, session, render_template, abort
from models.attendance.attendance_model import Attendance
from models.attendance.approval_flow import AttendanceApprovalFlow
from models.attendance.approval_status import AttendanceApprovalStatus
from models.hr.hr_profiles import HRProfile
from models.attendance.crew_model import CrewDefinition
from extensions import db
from datetime import datetime
from copy import deepcopy
from utils.auth_utils import login_required
from utils.attendance_log_utils import log_attendance_change_from_objects
import copy
from utils.approval_utils import get_approval_level_from_role
from utils.auth_utils import require_approval_roles
from utils.attendance_utils import update_ot_and_working_hours
import io
import pandas as pd
from flask import send_file

attendance_approval_bp = Blueprint("attendance_approval", __name__, url_prefix="/attendance/approval")


@attendance_approval_bp.route("/attendance/approval/approve/<int:attendance_id>", methods=["POST"])
@login_required
def approve_attendance(attendance_id):
    role = session.get("role", "").lower()
    user = session.get("username", "unknown")
    user_dept = session.get("department_code")

    status = AttendanceApprovalStatus.query.filter_by(AttendanceID=attendance_id).first()
    attendance = Attendance.query.filter_by(AttendanceID=attendance_id).first()

    if not status or not attendance:
        flash("Không tìm thấy bản ghi chấm công.", "danger")
        return redirect(url_for("attendance_approval.pending_approval"))

    # Kiểm tra phòng ban
    profile = HRProfile.query.filter_by(EmployeeID=attendance.EmployeeID).first()
    if profile and user_dept and profile.DepartmentCode != user_dept:
        return redirect(url_for("attendance_approval.pending_approval"))

    current_level = status.LastLevel

    if role in ("admin", "truongphong"):
        if current_level is not None:
            flash("Bạn không thể duyệt vì bản ghi đã qua bước này.", "warning")
            return redirect(url_for("attendance_approval.pending_approval"))

        status.Status = "Pending"
        status.LastLevel = 1
        status.LastAction = "Approved"
        status.LastModifiedBy = user
        status.LastModifiedAt = datetime.now()
        db.session.commit()
        flash("✅ Duyệt thành công (Cấp 1 - trưởng phòng)", "success")

    elif role in ("admin", "hanhchinh"):
        if current_level is None or status.LastAction != "Approved":
            flash("⚠️ Trưởng phòng chưa duyệt. Bạn chưa được phép duyệt.", "warning")
            return redirect(url_for("attendance_approval.pending_approval"))

        status.Status = "Approved"
        status.LastLevel = 2
        status.LastAction = "Approved"
        status.LastModifiedBy = user
        status.LastModifiedAt = datetime.now()

        old_data = copy.deepcopy(attendance)
        update_ot_and_working_hours(attendance)

        log_attendance_change_from_objects(
            attendance_before=old_data,
            attendance_after=attendance,
            edited_by=session.get("full_name", session.get("user_id", "unknown")),
            editor_role=session.get("role", "unknown"),
            source="Approval Cấp 2",
            change_type="Auto OT Split",
        )

        db.session.commit()
        flash("✅ Đã duyệt hoàn tất (Cấp 2 - Hành chính)", "success")

    else:
        abort(403)

    return redirect(url_for("attendance_approval.pending_approval"))


@attendance_approval_bp.route("/form/<int:attendance_id>")
@require_approval_roles("truongphong", "hanhchinh", "nhansu")
def show_approval_form(attendance_id):
    attendance = Attendance.query.get_or_404(attendance_id)
    approval_level = get_approval_level_from_role(session.get("role"))

    return render_template(
        "attendance/attendance_approval_form.html", attendance=attendance, approval_level=approval_level
    )


@attendance_approval_bp.route("/attendance/approval/reject/<int:attendance_id>", methods=["POST"])
@login_required
def reject_attendance(attendance_id):
    role = session.get("role", "").lower()
    user = session.get("username", "unknown")
    note = request.form.get("note", "")

    status = AttendanceApprovalStatus.query.filter_by(AttendanceID=attendance_id).first()

    if not status:
        flash("Không tìm thấy bản ghi duyệt.", "danger")
        return redirect(url_for("attendance_approval.pending_approval"))

    current_level = status.LastLevel

    # if role == "truongphong":
    if role in ("admin", "truongphong"):
        if current_level is not None:
            flash("Không thể từ chối vì bản ghi đã qua bước này.", "warning")
            return redirect(url_for("attendance_approval.pending_approval"))

        status.Status = "Rejected"
        status.LastLevel = 1
        status.LastAction = "Rejected"
        status.LastModifiedBy = user
        status.LastModifiedAt = datetime.now()
        status.Note = note
        db.session.commit()
        flash("🚫 Đã từ chối (Cấp 1 - trưởng phòng)", "success")

    elif role in ("admin", "hanhchinh"):
        if current_level != 1:
            flash("Bạn chỉ có thể từ chối sau khi trưởng phòng đã duyệt.", "warning")
            return redirect(url_for("attendance_approval.pending_approval"))

        status.Status = "Rejected"
        status.LastLevel = 2
        status.LastAction = "Rejected"
        status.LastModifiedBy = user
        status.LastModifiedAt = datetime.now()
        status.Note = note
        db.session.commit()
        flash("🚫 Đã từ chối (Cấp 2 - hành chính)", "success")

    else:
        abort(403)

    return redirect(url_for("attendance_approval.pending_approval"))


@attendance_approval_bp.route("/pending")
@require_approval_roles("truongphong", "hanhchinh")
def list_pending_approvals():

    approval_level = get_approval_level_from_role(session.get("role"))
    user_dept = session.get("department_code")

    # Lọc danh sách cần duyệt

    records = (
        db.session.query(
            Attendance,
            HRProfile.FullName,
            HRProfile.DepartmentCode,
            CrewDefinition.CrewName,
            AttendanceApprovalStatus.LastLevel,
        )
        .join(AttendanceApprovalStatus, Attendance.AttendanceID == AttendanceApprovalStatus.AttendanceID)
        .join(HRProfile, HRProfile.EmployeeID == Attendance.EmployeeID)
        .join(CrewDefinition, CrewDefinition.CrewID == Attendance.CrewID)
        .filter(
            AttendanceApprovalStatus.Status == "Pending",
            (AttendanceApprovalStatus.LastLevel == None) | (AttendanceApprovalStatus.LastLevel < approval_level),
        )
        .all()
    )

    enriched_records = []
    for row in records:
        att = row[0]
        att.FullName = row[1]
        att.DepartmentCode = row[2]
        att.CrewName = row[3]
        att.LastLevel = row[4]
        enriched_records.append(att)

    status_map = {s.AttendanceID: s.Status for s in AttendanceApprovalStatus.query.all()}

    return render_template(
        "attendance/approval_list_bulk.html",
        records=enriched_records,
        approval_level=approval_level,
        statuses=status_map,
    )


@attendance_approval_bp.route("/auditlog", methods=["GET"])
@require_approval_roles("truongphong", "hanhchinh", "nhansu")
def view_audit_log():
    from models.attendance.attendance_edit_log import AttendanceEditLog

    query = AttendanceEditLog.query

    employee_id = request.args.get("employee_id")
    edited_by = request.args.get("edited_by")
    change_type = request.args.get("change_type")
    field = request.args.get("field")

    if employee_id:
        query = query.filter(AttendanceEditLog.EmployeeID.ilike(f"%{employee_id}%"))
    if edited_by:
        query = query.filter(AttendanceEditLog.EditedBy.ilike(f"%{edited_by}%"))
    if change_type:
        query = query.filter(AttendanceEditLog.ChangeType == change_type)
    if field:
        query = query.filter(AttendanceEditLog.FieldChanged == field)

    logs = query.order_by(AttendanceEditLog.EditedAt.desc()).limit(100).all()
    return render_template("attendance/audit_log.html", logs=logs)


@attendance_approval_bp.route("/approved")
@require_approval_roles("truongphong", "hanhchinh", "nhansu")
def list_approved():
    records = (
        db.session.query(Attendance)
        .join(AttendanceApprovalStatus, Attendance.AttendanceID == AttendanceApprovalStatus.AttendanceID)
        .filter(AttendanceApprovalStatus.Status == "Approved")
        .order_by(Attendance.Date.desc())
        .all()
    )
    return render_template("attendance/approval_list_result.html", records=records, title="Danh sách đã duyệt")


@attendance_approval_bp.route("/rejected")
@require_approval_roles("truongphong", "hanhchinh", "nhansu")
def list_rejected():
    records = (
        db.session.query(Attendance)
        .join(AttendanceApprovalStatus, Attendance.AttendanceID == AttendanceApprovalStatus.AttendanceID)
        .filter(AttendanceApprovalStatus.Status == "Rejected")
        .order_by(Attendance.Date.desc())
        .all()
    )
    return render_template("attendance/approval_list_result.html", records=records, title="Danh sách bị từ chối")


@attendance_approval_bp.route("/auditlog/export")
def export_audit_log_excel():
    from models.attendance.attendance_edit_log import AttendanceEditLog

    query = AttendanceEditLog.query.order_by(AttendanceEditLog.EditedAt.desc())

    # Apply optional filters
    employee_id = request.args.get("employee_id")
    edited_by = request.args.get("edited_by")
    change_type = request.args.get("change_type")
    field = request.args.get("field")

    if employee_id:
        query = query.filter(AttendanceEditLog.EmployeeID.ilike(f"%{employee_id}%"))
    if edited_by:
        query = query.filter(AttendanceEditLog.EditedBy.ilike(f"%{edited_by}%"))
    if change_type:
        query = query.filter(AttendanceEditLog.ChangeType == change_type)
    if field:
        query = query.filter(AttendanceEditLog.FieldChanged == field)

    logs = query.all()

    # Chuyển sang DataFrame
    df = pd.DataFrame(
        [
            {
                "Thời gian sửa": log.EditedAt,
                "Mã NV": log.EmployeeID,
                "Người sửa": log.EditedBy,
                "Vai trò": log.EditorRole,
                "Nguồn": log.Source,
                "Loại thay đổi": log.ChangeType,
                "Trường sửa": log.FieldChanged,
                "Giờ vào (cũ)": log.OldCheckIn,
                "Giờ vào (mới)": log.NewCheckIn,
                "Giờ ra (cũ)": log.OldCheckOut,
                "Giờ ra (mới)": log.NewCheckOut,
                "Trạng thái (cũ)": log.OldStatus,
                "Trạng thái (mới)": log.NewStatus,
                "Ghi chú (cũ)": log.OldNote,
                "Ghi chú (mới)": log.NewNote,
            }
            for log in logs
        ]
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="AuditLog")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="AuditLog.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@attendance_approval_bp.route("/bulk/approve", methods=["POST"])
@require_approval_roles("truongphong", "hanhchinh", "nhansu")
def bulk_approve():
    ids = request.form.getlist("attendance_ids")
    approval_level = get_approval_level_from_role(session.get("role"))
    user = session.get("user_id", "unknown")

    count = 0
    for aid in ids:
        if not aid:
            continue
        try:
            aid_int = int(aid)
        except ValueError:
            continue

        attendance = Attendance.query.filter_by(AttendanceID=aid_int).first()
        if not attendance:
            continue

        status = AttendanceApprovalStatus.query.filter_by(AttendanceID=aid_int).first()
        if status and status.LastLevel is not None and status.LastLevel >= approval_level:
            continue

        approval = AttendanceApprovalFlow(
            AttendanceID=aid_int,
            ApprovalLevel=approval_level,
            Action="Approved",
            ApprovedBy=user,
            ApprovedAt=datetime.utcnow(),
            Note="Bulk approval",
        )
        db.session.add(approval)

        if not status:
            status = AttendanceApprovalStatus(AttendanceID=aid_int)
            db.session.add(status)

        if approval_level == 2:
            status.Status = "Approved"
        else:
            status.Status = "Pending"

        status.LastLevel = approval_level
        status.LastAction = "Approved"
        status.LastModifiedBy = user
        status.LastModifiedAt = approval.ApprovedAt
        count += 1

    db.session.commit()
    flash(f"✔️ Đã duyệt {count} bản ghi", "success")
    return redirect(url_for("attendance_approval.list_pending_approvals"))


@attendance_approval_bp.route("/bulk/reject", methods=["POST"])
@require_approval_roles("truongphong", "hanhchinh", "nhansu")
def bulk_reject():
    ids = request.form.getlist("attendance_ids")
    approval_level = get_approval_level_from_role(session.get("role"))
    user = session.get("user_id", "unknown")

    count = 0
    for aid in ids:
        if not aid:
            continue
        try:
            aid_int = int(aid)
        except ValueError:
            continue

        attendance = Attendance.query.filter_by(AttendanceID=aid_int).first()
        if not attendance:
            continue

        status = AttendanceApprovalStatus.query.filter_by(AttendanceID=aid_int).first()
        if status and status.LastLevel is not None and status.LastLevel >= approval_level:
            continue

        rejection = AttendanceApprovalFlow(
            AttendanceID=aid_int,
            ApprovalLevel=approval_level,
            Action="Rejected",
            ApprovedBy=user,
            ApprovedAt=datetime.utcnow(),
            Note="Bulk rejection",
        )
        db.session.add(rejection)

        if not status:
            status = AttendanceApprovalStatus(AttendanceID=aid_int)
            db.session.add(status)

        status.Status = "Rejected"
        status.LastLevel = approval_level
        status.LastAction = "Rejected"
        status.LastModifiedBy = user
        status.LastModifiedAt = rejection.ApprovedAt
        count += 1

    db.session.commit()
    flash(f"❌ Đã từ chối {count} bản ghi", "warning")
    return redirect(url_for("attendance_approval.list_pending_approvals"))
