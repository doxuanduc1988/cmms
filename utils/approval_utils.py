from pathlib import Path

# Tạo nội dung cho file utils/approval_utils.py


def get_approval_level_from_role(role: str) -> int:
    # Xác định cấp duyệt từ vai trò đăng nhập.
    role = role.lower() if role else ""
    return {"truongphong": 1, "hanhchinh": 2, "nhansu": 3}.get(role, 0)
