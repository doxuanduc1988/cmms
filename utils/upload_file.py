import os
from werkzeug.utils import secure_filename
from flask import current_app


def save_uploaded_file(file, subfolder, prefix="file"):
    """
    Lưu file upload vào static/uploads/<subfolder>/, tên file có tiền tố prefix.
    Trả về tên file nếu thành công, hoặc None nếu không có file.
    """
    if file and file.filename:
        filename = secure_filename(f"{prefix}_{file.filename}")
        base_path = current_app.root_path
        upload_path = os.path.join(base_path, "static", "uploads", subfolder)
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, filename))
        return filename
    return None


def delete_file_if_exists(subfolder, filename):
    """Xoá file trong static/uploads/<subfolder>/ nếu tồn tại"""
    if not filename:
        return
    base_path = current_app.root_path
    path = os.path.join(base_path, "static", "uploads", subfolder, filename)
    if os.path.exists(path):
        os.remove(path)
