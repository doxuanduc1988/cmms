from models.attendance.attendance_edit_log import AttendanceEditLog
from extensions import db
from datetime import datetime


def log_attendance_edit(
    attendance_id,
    employee_id,
    edited_by,
    old_checkin,
    old_checkout,
    old_status,
    old_note,
    new_checkin,
    new_checkout,
    new_status,
    new_note,
    change_type="Manual Edit",
    field_changed="Multiple",
    editor_role=None,
    source="Web UI",
):
    log = AttendanceEditLog(
        AttendanceID=attendance_id,
        EmployeeID=employee_id,
        EditedBy=edited_by,
        EditedAt=datetime.utcnow(),
        OldCheckIn=old_checkin,
        OldCheckOut=old_checkout,
        OldStatus=old_status,
        OldNote=old_note,
        NewCheckIn=new_checkin,
        NewCheckOut=new_checkout,
        NewStatus=new_status,
        NewNote=new_note,
        ChangeType=change_type,
        FieldChanged=field_changed,
        EditorRole=editor_role,
        Source=source,
    )
    db.session.add(log)
    db.session.commit()


def detect_changed_fields(old_data: dict, new_data: dict):

    # So sánh dữ liệu cũ và mới, trả về tên trường bị thay đổi hoặc 'Multiple'

    changed_fields = []
    for field in ["CheckIn", "CheckOut", "Status", "Note"]:
        if str(old_data.get(field)) != str(new_data.get(field)):
            changed_fields.append(field)

    if len(changed_fields) == 1:
        return changed_fields[0]
    elif len(changed_fields) > 1:
        return "Multiple"
    return "None"


def log_attendance_change_from_objects(
    attendance_before, attendance_after, edited_by, editor_role=None, source="Web UI", change_type="Manual Edit"
):

    # So sánh hai bản ghi Attendance (trước và sau), ghi log nếu có thay đổi.

    old_data = {
        "CheckIn": str(attendance_before.CheckInTime),
        "CheckOut": str(attendance_before.CheckOutTime),
        "Status": attendance_before.Status,
        "Note": attendance_before.Note,
    }

    new_data = {
        "CheckIn": str(attendance_after.CheckInTime),
        "CheckOut": str(attendance_after.CheckOutTime),
        "Status": attendance_after.Status,
        "Note": attendance_after.Note,
    }

    field_changed = detect_changed_fields(old_data, new_data)

    if field_changed == "None":
        return  # Không có thay đổi, không cần ghi log

    log_attendance_edit(
        attendance_id=attendance_before.AttendanceID,
        employee_id=attendance_before.EmployeeID,
        edited_by=edited_by,
        old_checkin=old_data["CheckIn"],
        old_checkout=old_data["CheckOut"],
        old_status=old_data["Status"],
        old_note=old_data["Note"],
        new_checkin=new_data["CheckIn"],
        new_checkout=new_data["CheckOut"],
        new_status=new_data["Status"],
        new_note=new_data["Note"],
        change_type=change_type,
        field_changed=field_changed,
        editor_role=editor_role,
        source=source,
    )
