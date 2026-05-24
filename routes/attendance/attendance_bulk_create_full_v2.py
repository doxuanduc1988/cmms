from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.attendance.attendance_model import Attendance
from models.attendance.approval_status import AttendanceApprovalStatus
from models.hr.department_model import Department
from models.attendance.crew_model import CrewDefinition
from models.hr.hr_profiles import HRProfile
from models.crew_assignment import CrewAssignment
from models.attendance.shift_model import ShiftDefinition
from config import ENFORCE_DATE_LOCK
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import and_, distinct
from utils.attendance_validation_utils import validate_bulk_attendance
from utils.attendance_utils import update_ot_and_working_hours
from utils.attendance_log_utils import log_attendance_edit
from utils.auth_utils import login_required
from utils.permission_utils import check_permission, get_data_scope, user_is_system_admin


# from flask import abort


attendance_bulk_bp = Blueprint("attendance_bulk", __name__, url_prefix="/attendance/bulk")

status_choices = [
    ("Working", "Đi làm"),
    ("Leave", "Nghỉ phép"),
    ("SickLeave", "Nghỉ ốm"),
    ("Holiday", "Nghỉ lễ"),
    ("CompensatoryLeave", "Nghỉ bù"),
    ("Absent", "Vắng mặt"),
    ("OT", "Ngoài giờ"),
]

SHIFT_TIME_DEFAULTS = {
    1: ("06:00", "14:00"),
    2: ("14:00", "22:00"),
    3: ("22:00", "06:00"),
    4: ("08:00", "17:00"),
}


@attendance_bulk_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("attendance", "create")
def bulk_create_attendance():
    user_dept = session.get("department_code")
    scope = get_data_scope("attendance")

    if scope == "all" or user_is_system_admin():
        departments = Department.query.all()
        crews = CrewDefinition.query.all()
    else:
        departments = Department.query.filter_by(DepartmentCode=user_dept).all() if user_dept else []
        # 🔍 Lọc danh sách CrewID theo CrewAssignments thuộc phòng của user
        assigned_crews = (
            db.session.query(distinct(CrewAssignment.CrewID)).filter(CrewAssignment.DepartmentCode == user_dept).all()
        )
        crew_ids = [row[0] for row in assigned_crews]
        crews = CrewDefinition.query.filter(CrewDefinition.CrewID.in_(crew_ids)).order_by(CrewDefinition.CrewID).all()

    shifts = ShiftDefinition.query.all()

    if request.method == "POST":
        selected_date = request.form.get("selected_date") or datetime.today().strftime("%Y-%m-%d")
        if ENFORCE_DATE_LOCK:
            today = datetime.today().date()
            target_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            if target_date < today - timedelta(days=3) or target_date > today:
                flash("⚠️ Chỉ được phép chấm công trong vòng 3 ngày gần nhất!", "danger")
                return redirect(url_for("attendance_bulk.bulk_create_attendance"))

        shift_id = int(request.form.get("shift_id"))
        department_code = request.form.get("department_code")
        crew_id = request.form.get("crew_id")

        # 🔒 Phạm vi phòng ban / cá nhân
        scope = get_data_scope("attendance")
        if scope == "self":
            abort(403)
        if scope == "department" and user_dept and department_code != user_dept:
            return redirect(url_for("attendance_bulk.bulk_create_attendance"))

        # Lọc danh sách nhân viên theo CrewAssignment nếu có crew_id
        if crew_id:
            assignments = CrewAssignment.query.filter(
                CrewAssignment.CrewID == crew_id,
                CrewAssignment.DepartmentCode == department_code,
                CrewAssignment.StartDate <= selected_date,
                CrewAssignment.EndDate >= selected_date,
            ).all()
            employee_ids = [a.EmployeeID for a in assignments]
            query = HRProfile.query.filter(HRProfile.EmployeeID.in_(employee_ids))
        else:
            query = HRProfile.query
            if department_code:
                query = query.filter(HRProfile.DepartmentCode == department_code)

        employees = query.order_by(HRProfile.FullName).all()
        check_in, check_out = SHIFT_TIME_DEFAULTS.get(shift_id, ("08:00", "17:00"))

        count = 0
        for emp in employees:
            new_att = Attendance(
                EmployeeID=emp.EmployeeID,
                Date=selected_date,
                ShiftID=shift_id,
                CrewID=emp.CrewID or crew_id,
                DepartmentCode=emp.DepartmentCode or department_code,
                CheckInTime=check_in,
                CheckOutTime=check_out,
                Status="Working",
            )
            update_ot_and_working_hours(new_att)
            db.session.add(new_att)
            db.session.flush()  # Lấy AttendanceID

            status = AttendanceApprovalStatus(
                AttendanceID=new_att.AttendanceID,
                Status="Pending",
                LastLevel=None,
                LastAction=None,
                LastModifiedBy=session.get("username", "system"),
                LastModifiedAt=datetime.now(),
            )
            db.session.add(status)
            count += 1

        db.session.commit()
        flash(f"✔️ Đã chấm công và tạo duyệt cho {count} nhân sự!", "success")
        return redirect(url_for("attendance_bulk.bulk_create_attendance"))

    return render_template(
        "attendance/attendance_bulk_select.html", departments=departments, crews=crews, shifts=shifts, submit_mode=False
    )


@attendance_bulk_bp.route("/save", methods=["POST"])
@login_required
@check_permission("attendance", "create")
def bulk_save_attendance():
    user_dept = session.get("department_code")
    scope = get_data_scope("attendance")
    if scope == "self":
        abort(403)

    selected_date = request.form.get("selected_date")
    shift_id = request.form.get("shift_id")
    department_code = request.form.get("department_code")
    crew_id = request.form.get("crew_id")
    employee_ids = request.form.getlist("employee_ids")

    errors = validate_bulk_attendance(employee_ids, selected_date, request.form)
    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(
            url_for(
                "attendance_bulk.bulk_create_attendance",
                selected_date=selected_date,
                department_code=department_code,
                shift_id=shift_id,
                crew_id=crew_id,
            )
        )

    for emp_id in employee_ids:
        status = request.form.get(f"status_{emp_id}", "Working")
        note = request.form.get(f"note_{emp_id}", "")
        check_in_time = request.form.get(f"check_in_time_{emp_id}")
        check_out_time = request.form.get(f"check_out_time_{emp_id}")

        profile = HRProfile.query.filter_by(EmployeeID=emp_id).first()
        dept_code = profile.DepartmentCode if profile and profile.DepartmentCode else "WAICODE"
        if dept_code == "WAICODE":
            flash(f"⚠ Nhân viên {emp_id} chưa có mã phòng ban trong HRProfiles – đang tạm gán WAICODE", "warning")

        time_fmt = "%H:%M"
        t_start = datetime.strptime(check_in_time, time_fmt)
        t_end = datetime.strptime(check_out_time, time_fmt)
        total_hours = (t_end - t_start).total_seconds() / 3600

        if total_hours > 8:
            work_end = (t_start + timedelta(hours=8)).time()
            attendance_main = Attendance(
                EmployeeID=emp_id,
                Date=datetime.strptime(selected_date, "%Y-%m-%d").date(),
                ShiftID=shift_id,
                DepartmentCode=dept_code,
                CrewID=crew_id,
                CheckInTime=check_in_time,
                CheckOutTime=work_end.strftime("%H:%M"),
                Status="Working",
                Note=note + " [Tự động tách OT]" if note else "[Tự động tách OT]",
            )
            update_ot_and_working_hours(attendance_main)
            db.session.add(attendance_main)

            ot_start = work_end
            ot_end = t_end.time()
            attendance_ot = Attendance(
                EmployeeID=emp_id,
                Date=datetime.strptime(selected_date, "%Y-%m-%d").date(),
                ShiftID=shift_id,
                DepartmentCode=dept_code,
                CrewID=crew_id,
                CheckInTime=ot_start.strftime("%H:%M"),
                CheckOutTime=ot_end.strftime("%H:%M"),
                Status="OT",
                Note="Tự động tạo OT",
            )
            update_ot_and_working_hours(attendance_ot)
            db.session.add(attendance_ot)
        else:
            attendance = Attendance(
                EmployeeID=emp_id,
                Date=datetime.strptime(selected_date, "%Y-%m-%d").date(),
                ShiftID=shift_id,
                DepartmentCode=dept_code,
                CrewID=crew_id,
                CheckInTime=check_in_time,
                CheckOutTime=check_out_time,
                Status=status,
                Note=note,
            )
            update_ot_and_working_hours(attendance)
            db.session.add(attendance)
            db.session.flush()  # Để lấy AttendanceID nếu cần

            log_attendance_edit(
                attendance,
                action="Create",
                edited_by=session.get("full_name", session.get("user_id", "unknown")),
                note="Tạo từ form nhóm",
                source="Chấm công nhóm",
            )

    db.session.commit()
    flash("✅ Đã lưu chấm công nhóm thành công!", "success")
    return redirect(url_for("attendance_bulk.bulk_create_attendance"))
