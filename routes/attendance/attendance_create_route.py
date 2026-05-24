from flask import Blueprint, request, render_template, redirect, url_for, session, abort, flash
from models.attendance.attendance_model import Attendance
from models.attendance.approval_status import AttendanceApprovalStatus
from models.hr.hr_profiles import HRProfile
from extensions import db
from datetime import datetime, timedelta
from utils.attendance_utils import update_ot_and_working_hours
from config import ENFORCE_DATE_LOCK
from utils.attendance_log_utils import log_attendance_edit
from flask_login import login_required
from utils.permission_utils import check_permission

attendance_create_bp = Blueprint("attendance_create", __name__, url_prefix="/attendance")


def estimate_shift_id(check_in):
    if not check_in:
        return 0
    hour = check_in.hour
    if 5 <= hour < 12:
        return 1
    elif 12 <= hour < 18:
        return 2
    elif hour >= 18 or hour < 5:
        return 3
    return 0


@attendance_create_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("attendance", "create")
def create_attendance():
    emp_id = request.args.get("employee_id") if request.method == "GET" else request.form.get("EmployeeID")
    date = request.args.get("date") if request.method == "GET" else request.form.get("Date")
    employee = HRProfile.query.filter_by(EmployeeID=emp_id).first() if emp_id else None
    # employees = HRProfile.query.order_by(HRProfile.FullName).all()

    user_dept = session.get("department_code")
    if role in ("admin", "nhansu"):
        employees = HRProfile.query.order_by(HRProfile.FullName).all()
    else:
        employees = HRProfile.query.filter_by(DepartmentCode=user_dept).order_by(HRProfile.FullName).all()

    if request.method == "POST":
        if not emp_id or not date:
            flash("Thiếu thông tin nhân viên hoặc ngày chấm công.", "danger")
            return redirect(url_for("attendance_create.create_attendance"))

        if ENFORCE_DATE_LOCK:
            today = datetime.today().date()
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            if target_date < today - timedelta(days=3) or target_date > today:
                flash("Chỉ được chấm công trong vòng 3 ngày gần nhất!", "danger")
                return redirect(url_for("attendance_create.create_attendance", employee_id=emp_id, date=date))

        # 🔐 Kiểm tra phân quyền theo phòng/kíp (Bỏ qua cho Admin/Nhansu)
        user_dept = session.get("department_code")
        user_crew = session.get("crew_id")
        if role not in ("admin", "nhansu") and employee:
            if employee.DepartmentCode and user_dept and employee.DepartmentCode != user_dept:
                return redirect(url_for("attendance_create.create_attendance"))
            if employee.CrewID and user_crew and employee.CrewID != user_crew:
                return redirect(url_for("attendance_create.create_attendance"))

        check_in = request.form.get("CheckInTime") or request.form.get("start_time")
        check_out = request.form.get("CheckOutTime") or request.form.get("end_time")

        check_in_time = datetime.strptime(check_in, "%H:%M").time() if check_in else None
        check_out_time = datetime.strptime(check_out, "%H:%M").time() if check_out else None

        crew_id = employee.CrewID if employee and employee.CrewID else "7"
        dept_code = employee.DepartmentCode if employee and employee.DepartmentCode else "WAITCODE"
        shift_id = estimate_shift_id(check_in_time)

        # 🔍 Kiểm tra có attendance cũ không
        existing = Attendance.query.filter_by(EmployeeID=emp_id, Date=date).first()

        if existing:
            old_checkin = existing.CheckInTime
            old_checkout = existing.CheckOutTime
            old_status = existing.Status

            existing.CheckInTime = check_in_time
            existing.CheckOutTime = check_out_time
            existing.ShiftID = shift_id
            existing.Status = request.form.get("status", "Working")
            existing.CrewID = crew_id
            existing.DepartmentCode = dept_code

            update_ot_and_working_hours(existing)
            db.session.commit()

            log_attendance_edit(
                attendance_id=existing.AttendanceID,
                employee_id=emp_id,
                edited_by=session.get("full_name", session.get("user_id", "unknown")),
                old_checkin=old_checkin.strftime("%H:%M") if old_checkin else None,
                old_checkout=old_checkout.strftime("%H:%M") if old_checkout else None,
                old_status=old_status,
                old_note=existing.Note,
                new_checkin=check_in,
                new_checkout=check_out,
                new_status=existing.Status,
                new_note=existing.Note,
                change_type="Updated",
                field_changed="All",
                editor_role=session.get("role", "unknown"),
                source="Web UI",
            )

        else:
            attendance = Attendance(
                EmployeeID=emp_id,
                Date=date,
                ShiftID=shift_id,
                CrewID=crew_id,
                DepartmentCode=dept_code,
                CheckInTime=check_in_time,
                CheckOutTime=check_out_time,
                Status=request.form.get("status", "Working"),
            )

            update_ot_and_working_hours(attendance)
            db.session.add(attendance)
            db.session.flush()

            status = AttendanceApprovalStatus(
                AttendanceID=attendance.AttendanceID,
                Status="Pending",
                LastLevel=None,
                LastAction=None,
                LastModifiedBy=session.get("username", "system"),
                LastModifiedAt=datetime.now(),
            )
            db.session.add(status)
            db.session.commit()

            log_attendance_edit(
                attendance_id=attendance.AttendanceID,
                employee_id=emp_id,
                edited_by=session.get("full_name", session.get("user_id", "unknown")),
                old_checkin=None,
                old_checkout=None,
                old_status=None,
                old_note=None,
                new_checkin=check_in,
                new_checkout=check_out,
                new_status=attendance.Status,
                new_note="",
                change_type="Created",
                field_changed="All",
                editor_role=session.get("role", "unknown"),
                source="Web UI",
            )

        return redirect(url_for("attendance_create.create_attendance", employee_id=emp_id, date=date))

    return render_template(
        "attendance/attendance_create_form.html", employee_id=emp_id, date=date, employee=employee, employees=employees
    )
