from flask import Blueprint, request, redirect, url_for, flash
from models.attendance.attendance_model import Attendance
from extensions import db
from datetime import datetime, time

MAX_WORK_HOURS_PER_DAY = 12
MAIN_STATUSES = ["Working", "Leave", "SickLeave", "Holiday", "CompensatoryLeave"]


def is_overlap(start1, end1, start2, end2):
    return max(start1, start2) < min(end1, end2)


def to_time(value):
    if isinstance(value, time):
        return value
    elif isinstance(value, str):
        return datetime.strptime(value, "%H:%M").time()
    raise ValueError("Giá trị giờ không hợp lệ")


def calc_hours(t1, t2):
    dt1 = datetime.combine(datetime.today(), t1)
    dt2 = datetime.combine(datetime.today(), t2)
    delta = dt2 - dt1
    return delta.total_seconds() / 3600


def validate_attendance(employee_id, date, check_in, check_out, crew_id, current_status):

    existing = Attendance.query.filter(Attendance.EmployeeID == employee_id, Attendance.Date == date).all()

    try:
        new_start = to_time(check_in)
        new_end = to_time(check_out)
    except Exception:
        return f"❌ Nhập sai định dạng giờ cho nhân viên {employee_id}"

    new_hours = calc_hours(new_start, new_end)
    total_hours = new_hours

    # Nếu đang chấm công OT → cần có ca chính
    if current_status.lower() in ["ot", "overtime"]:
        has_main = any(r.Status in MAIN_STATUSES for r in existing)
        if not has_main:
            return f"❌ Nhân viên {employee_id} không thể chấm OT khi chưa có ca chính trong ngày {date}"

    for record in existing:
        if not record.CheckInTime or not record.CheckOutTime:
            continue
        try:
            old_start = to_time(record.CheckInTime)
            old_end = to_time(record.CheckOutTime)
        except Exception:
            continue

        # Trùng giờ
        if is_overlap(new_start, new_end, old_start, old_end):
            return (
                f"❌ Nhân viên {employee_id} đã được chấm công từ {old_start.strftime('%H:%M')} đến {old_end.strftime('%H:%M')}, "
                f"không thể chấm thêm từ {new_start.strftime('%H:%M')} đến {new_end.strftime('%H:%M')}."
            )

        # Kiểm tra chấm ở nhiều kíp
        if record.CrewID and crew_id and str(record.CrewID) != str(crew_id):
            return (
                f"❌ Nhân viên {employee_id} đã được chấm công trong kíp khác (CrewID = {record.CrewID}) "
                f"trong ngày {date}, không thể thuộc nhiều kíp."
            )

        total_hours += calc_hours(old_start, old_end)

    if total_hours > MAX_WORK_HOURS_PER_DAY:
        return (
            f"❌ Nhân viên {employee_id} có tổng số giờ làm trong ngày {date} là {round(total_hours, 2)}h "
            f"(vượt quá giới hạn {MAX_WORK_HOURS_PER_DAY}h/ngày)"
        )

    return None


def validate_bulk_attendance(employee_ids, selected_date, request_form):
    crew_id = request_form.get("crew_id")
    errors = []
    for emp_id in employee_ids:
        check_in = request_form.get(f"check_in_time_{emp_id}")
        check_out = request_form.get(f"check_out_time_{emp_id}")
        status = request_form.get(f"status_{emp_id}", "Working")
        if not check_in or not check_out:
            continue
        error = validate_attendance(emp_id, selected_date, check_in, check_out, crew_id, status)
        if error:
            errors.append(error)
    return errors
