# Cấu hình tính năng bảo vệ ngày chấm công
ENFORCE_DATE_LOCK = False  # Đặt True nếu muốn giới hạn chấm công chỉ trong vòng 3 ngày

# Cấu hình thư mục upload phiếu khám sức khỏe
UPLOAD_FOLDER_HEALTH = "static/uploads/health_docs"

UPLOAD_SUBFOLDER_HEALTH = "health_docs"
UPLOAD_SUBFOLDER_CONTRACTS = "contracts"
UPLOAD_SUBFOLDER_EDUCATION = "certificates"
import os
import platform

# Cấu hình đường dẫn wkhtmltopdf linh hoạt
if platform.system() == "Windows":
    WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
else:
    WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH", "/usr/bin/wkhtmltopdf")

