from datetime import datetime, timedelta
from models import db
from models.attendance.attendance_edit_log import AttendanceEditLog


def parse_time_safe(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%H:%M:%S").time()
        except ValueError:
            return datetime.strptime(value, "%H:%M").time()
    return value  # đã là datetime.time


def update_ot_and_working_hours(attendance):

    # Tự động tính WorkingHours và OvertimeHours từ CheckInTime và CheckOutTime
    if not attendance.CheckInTime or not attendance.CheckOutTime:
        attendance.WorkingHours = 0
        attendance.OvertimeHours = 0
        return

    check_in = parse_time_safe(attendance.CheckInTime)
    check_out = parse_time_safe(attendance.CheckOutTime)

    if check_in and check_out:
        t1 = datetime.combine(datetime.today(), check_in)
        t2 = datetime.combine(datetime.today(), check_out)
        if t2 <= t1:
            t2 += timedelta(days=1)  # ca đêm

        total_hours = (t2 - t1).total_seconds() / 3600

        # Trừ 1h nghỉ trưa nếu ca hành chính (08:00–17:00)
        if (
            check_in <= datetime.strptime("09:00", "%H:%M").time()
            and check_out >= datetime.strptime("17:00", "%H:%M").time()
        ):
            total_hours -= 1

        total_hours = max(total_hours, 0)

        attendance.WorkingHours = round(min(total_hours, 8), 2)
        attendance.OvertimeHours = round(max(total_hours - 8, 0), 2)
    else:
        attendance.WorkingHours = 0
        attendance.OvertimeHours = 0


def log_attendance_edit(attendance_id, edited_by, old_data, new_data, change_type="ManualEdit"):
    changed_fields = []

    # So sánh từng trường để phát hiện thay đổi
    if old_data.CheckInTime != new_data.CheckInTime:
        changed_fields.append("CheckInTime")
    if old_data.CheckOutTime != new_data.CheckOutTime:
        changed_fields.append("CheckOutTime")
    if old_data.Status != new_data.Status:
        changed_fields.append("Status")
    if old_data.Note != new_data.Note:
        changed_fields.append("Note")

    # Nếu không thay đổi gì, không ghi log
    if not changed_fields:
        return

    log = AttendanceEditLog(
        AttendanceID=attendance_id,
        EditedBy=edited_by,
        EditedAt=datetime.now(),
        OldCheckIn=old_data.CheckInTime,
        OldCheckOut=old_data.CheckOutTime,
        OldStatus=old_data.Status,
        OldNote=old_data.Note,
        NewCheckIn=new_data.CheckInTime,
        NewCheckOut=new_data.CheckOutTime,
        NewStatus=new_data.Status,
        NewNote=new_data.Note,
        ChangeType=change_type,
        EmployeeID=old_data.EmployeeID,
        FieldChanged=", ".join(changed_fields),
    )

    db.session.add(log)
