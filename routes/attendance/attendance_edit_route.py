from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.attendance.attendance_model import Attendance
from models.hr.hr_profiles import HRProfile
from extensions import db
from config import ENFORCE_DATE_LOCK
from flask import flash
from utils.attendance_utils import update_ot_and_working_hours, log_attendance_edit
from datetime import datetime, timedelta

# from models.attendance.attendance_edit_log import AttendanceEditLog  # --> vì đã có log_attendance_change_from_objects
import copy
from models import db
from utils.attendance_log_utils import log_attendance_change_from_objects

attendance_edit_bp = Blueprint("attendance_edit", __name__, url_prefix="/attendance")


@attendance_edit_bp.route("/edit/<int:attendance_id>", methods=["GET", "POST"])
def edit_attendance(attendance_id):
    role = session.get("role", "").lower()
    if role not in ("admin", "nhansu", "hanhchinh"):
        abort(403)

    attendance = Attendance.query.get_or_404(attendance_id)

    # ✅ Bổ sung dòng sau để ép join HRProfile
    attendance.employee = HRProfile.query.filter_by(EmployeeID=attendance.EmployeeID).first()

    if request.method == "POST":
        # Kiểm tra giới hạn ngày chỉnh sửa nếu bật bảo vệ
        if ENFORCE_DATE_LOCK:
            today = datetime.today().date()
            if attendance.Date < today - timedelta(days=3) or attendance.Date > today:
                flash("❌ Chỉ được sửa công trong vòng 3 ngày gần nhất!", "danger")
                return redirect(url_for("attendance_edit.edit_attendance", attendance_id=attendance_id))

        # Sao lưu bản gốc để log thay đổi
        old_data = copy.deepcopy(attendance)

        # Lấy dữ liệu mới từ form
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        status = request.form.get("status")
        note = request.form.get("note")

        attendance.CheckInTime = check_in
        attendance.CheckOutTime = check_out
        attendance.Status = status
        attendance.Note = note

        # Ép kiểu giờ nếu cần và cập nhật OT
        update_ot_and_working_hours(attendance)  # Luôn tính lại dù là Working hay OT

        # Ghi log nếu có thay đổi
        log_attendance_change_from_objects(
            attendance_before=old_data,
            attendance_after=attendance,
            # edited_by=session.get("user_id", "unknown"),
            edited_by=session.get("full_name", session.get("user_id", "unknown")),
            editor_role=session.get("role", "unknown"),  # hoặc suy ra từ role hiện tại
            source="Web UI",
            change_type="Manual Edit",
        )

        db.session.commit()
        flash("✅ Cập nhật thành công và đã ghi log chỉnh sửa.", "success")
        return redirect(url_for("attendance_check.check_attendance"))

    return render_template("attendance/attendance_edit_form.html", attendance=attendance)
