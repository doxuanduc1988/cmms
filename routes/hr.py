from sqlalchemy import or_
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.hr.hr_profiles import HRProfile
from models.hr.department_model import Department
from models.hr.job_position_model import JobPosition

from utils.permission_utils import apply_department_scope, check_permission
from routes.hr_salary_history import salary_history_bp
from werkzeug.utils import secure_filename

import os
from PIL import Image, ImageOps
from datetime import datetime
from models.hr.dependent import HRDependent

from utils.salary_utils import get_latest_coefficient

# Thêm dòng này vào nhóm import models
from models.hr_salary_history import HRSalaryHistory

hr_bp = Blueprint("hr", __name__, url_prefix="/hr")
UPLOAD_PHOTO_ROOT = os.path.join(os.getcwd(), "static", "uploads", "hr_pics")
os.makedirs(UPLOAD_PHOTO_ROOT, exist_ok=True)


# Danh sách hồ sơ
@hr_bp.route("/")
@login_required
@check_permission("hr", "read")
def list_profiles():

    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # JOIN sang JobPosition & Department (outer join để không mất bản ghi thiếu FK)
    query = HRProfile.query.join(JobPosition, HRProfile.JobPositionID == JobPosition.JobPositionID, isouter=True).join(
        Department, HRProfile.DepartmentCode == Department.DepartmentCode, isouter=True
    )
    query = apply_department_scope(query, HRProfile, module_code="hr")

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                HRProfile.FullName.ilike(term),  # Họ tên
                HRProfile.EmployeeID.ilike(term),  # Mã NV
                HRProfile.StaffCode.ilike(term),  # Mã thẻ/mã nội bộ (nếu dùng)
                JobPosition.JobPositionName.ilike(term),  # Vị trí
                Department.DepartmentName.ilike(term),  # Tên đơn vị
                Department.DepartmentCode.ilike(term),  # Mã đơn vị (VD: TB2_KHTC)
            )
        )

    # distinct() để tránh trùng dòng khi join (an toàn cho future)
    profiles = query.distinct().order_by(HRProfile.FullName.asc()).paginate(page=page, per_page=per_page)

    return render_template("hr/list.html", profiles=profiles, search=search)

    # Chi tiết hồ sơ


@hr_bp.route("/detail/<string:employee_id>")
@login_required
@check_permission("hr", "read")
def profile_detail(employee_id):
    profile = HRProfile.query.get_or_404(employee_id)
    return render_template("hr/detail.html", profile=profile)


# Tạo hồ sơ mới
@hr_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("hr", "create")
def create_profile():
    # departments = Department.query.all()
    departments = Department.query.order_by(Department.DepartmentCode).all()
    job_positions = JobPosition.query.all()

    if request.method == "POST":
        try:
            profile = HRProfile(
                EmployeeID=request.form["EmployeeID"],
                FullName=request.form["FullName"],
                Gender=request.form.get("Gender"),
                StaffCode=request.form.get("StaffCode"),
                Nationality=request.form.get("Nationality"),
                Ethnicity=request.form.get("Ethnicity"),
                ResidenceAddress=request.form.get("ResidenceAddress"),
                IDNumber=request.form.get("IDNumber"),
                IDIssuedDate=request.form.get("IDIssuedDate") or None,
                IDIssuedPlace=request.form.get("IDIssuedPlace"),
                InsuranceNumber=request.form.get("InsuranceNumber"),
                InsuranceIssuedDate=request.form.get("InsuranceIssuedDate") or None,
                TaxCode=request.form.get("TaxCode"),
                TaxIssuedDate=request.form.get("TaxIssuedDate") or None,
                TechnicalLevel=request.form.get("TechnicalLevel"),
                # JobPosition=request.form.get("JobPosition"),
                JobPositionID=request.form.get("JobPositionID"),
                DepartmentCode=request.form.get("DepartmentCode"),
                ContractNumber=request.form.get("ContractNumber"),
                ContractType=request.form.get("ContractType"),
                StartDate=request.form.get("StartDate") or None,
                Salary=request.form.get("Salary") or 0,
                RegionAllowance=request.form.get("RegionAllowance") or 0,
                SalaryHistory=request.form.get("SalaryHistory"),
                WorkHistory=request.form.get("WorkHistory"),
                Dependents=request.form.get("Dependents"),
                BankAccount=request.form.get("BankAccount"),
                PaymentMethod=request.form.get("PaymentMethod"),
                LeavePolicy=request.form.get("LeavePolicy"),
                AnnualLeaveDays=request.form.get("AnnualLeaveDays") or 0,
                LeaveReason=request.form.get("LeaveReason"),
                OvertimeHours=request.form.get("OvertimeHours") or 0,
                InsuranceStatus=request.form.get("InsuranceStatus"),
                Training=request.form.get("Training"),
                Discipline=request.form.get("Discipline"),
                WorkInjury=request.form.get("WorkInjury"),
                TerminationDate=request.form.get("TerminationDate") or None,
                TerminationReason=request.form.get("TerminationReason"),
                Notes=request.form.get("Notes"),
                Email=request.form.get("Email"),
                Phone=request.form.get("Phone"),
                EmergencyContactName=request.form.get("EmergencyContactName"),
                EmergencyContactPhone=request.form.get("EmergencyContactPhone"),
                EndDate=request.form.get("EndDate") or None,
                SalaryGrade=request.form.get("SalaryGrade"),
            )
            db.session.add(profile)
            db.session.commit()
            flash("✅ Tạo hồ sơ nhân sự thành công.", "success")
            return redirect(url_for("hr.list_profiles"))
        except IntegrityError:
            db.session.rollback()
            flash("❌ Mã EmployeeID đã tồn tại!", "danger")

    return render_template("hr/create.html", departments=departments, job_positions=job_positions)


# Sửa hồ sơ
@hr_bp.route("/edit/<string:employee_id>", methods=["GET", "POST"])
@login_required
@check_permission("hr", "update")  # Hoặc phân quyền bao trùm
def edit_profile(employee_id):
    profile = HRProfile.query.get_or_404(employee_id)
    departments = Department.query.order_by(Department.DepartmentCode).all()
    job_positions = JobPosition.query.all()

    if request.method == "POST":
        # Xử lý ảnh: lưu theo thư mục năm/tháng và resize
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            ext = os.path.splitext(photo_file.filename)[1].lower()
            today = datetime.today()
            subdir = os.path.join(str(today.year), f"{today.month:02d}")
            full_folder = os.path.join(UPLOAD_PHOTO_ROOT, subdir)
            os.makedirs(full_folder, exist_ok=True)

            filename = f"{employee_id}{ext}"
            photo_path = os.path.join(full_folder, filename)
            new_relative_path = f"{subdir.replace(os.sep, '/')}/{filename}"

            # Xoá ảnh cũ nếu khác tên
            if profile.Photo and profile.Photo != new_relative_path:
                old_path = os.path.join(UPLOAD_PHOTO_ROOT, profile.Photo.replace("/", os.sep))
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Resize ảnh trước khi lưu (240x320)
            image = Image.open(photo_file)
            resized = ImageOps.fit(image, (240, 320), Image.LANCZOS)
            resized.save(photo_path)

            # profile.Photo = f"{subdir.replace(os.sep, '/')}/{filename}"
            profile.Photo = new_relative_path

        # 👤 Thông tin cá nhân
        profile.FullName = request.form.get("FullName")
        profile.Gender = request.form.get("Gender")
        profile.DateOfBirth = request.form.get("DateOfBirth")
        profile.PlaceOfBirth = request.form.get("PlaceOfBirth")

        # 📞 Liên hệ
        profile.Email = request.form.get("Email")
        profile.Phone = request.form.get("Phone")

        # 📄 Hợp đồng
        profile.ContractNumber = request.form.get("ContractNumber")
        profile.ContractType = request.form.get("ContractType")

        # 💸 Lương
        profile.Salary = request.form.get("Salary") or 0
        profile.RegionAllowance = request.form.get("RegionAllowance") or 1

        # 🛡 Bảo hiểm
        profile.InsuranceNumber = request.form.get("InsuranceNumber")
        profile.TaxCode = request.form.get("TaxCode")

        # ⛱ Nghỉ phép
        profile.AnnualLeaveDays = request.form.get("AnnualLeaveDays") or 0

        # 📚 Đào tạo
        profile.Training = request.form.get("Training")

        # 📝 Ghi chú
        profile.Notes = request.form.get("Notes")

        profile.StaffCode = request.form.get("StaffCode")
        profile.Nationality = request.form.get("Nationality")
        profile.Ethnicity = request.form.get("Ethnicity")
        profile.ResidenceAddress = request.form.get("ResidenceAddress")
        profile.IDNumber = request.form.get("IDNumber")
        profile.IDIssuedDate = request.form.get("IDIssuedDate") or None
        profile.IDIssuedPlace = request.form.get("IDIssuedPlace")

        profile.TaxCode = request.form.get("TaxCode")
        profile.TaxIssuedDate = request.form.get("TaxIssuedDate") or None
        profile.TechnicalLevel = request.form.get("TechnicalLevel")

        profile.DepartmentCode = request.form.get("DepartmentCode")
        profile.JobPositionID = request.form.get("JobPositionID")

        profile.StartDate = request.form.get("StartDate") or None

        profile.SalaryHistory = request.form.get("SalaryHistory")
        profile.WorkHistory = request.form.get("WorkHistory")
        profile.Dependents = request.form.get("Dependents")
        profile.BankAccount = request.form.get("BankAccount")
        profile.LeavePolicy = request.form.get("LeavePolicy")

        profile.LeaveReason = request.form.get("LeaveReason")
        profile.OvertimeHours = request.form.get("OvertimeHours") or 0
        profile.InsuranceStatus = request.form.get("InsuranceStatus")

        profile.Discipline = request.form.get("Discipline")
        profile.WorkInjury = request.form.get("WorkInjury")
        profile.TerminationDate = request.form.get("TerminationDate") or None
        profile.TerminationReason = request.form.get("TerminationReason")
        profile.EmergencyContactName = request.form.get("EmergencyContactName")
        profile.EmergencyContactPhone = request.form.get("EmergencyContactPhone")
        profile.EndDate = request.form.get("EndDate") or None
        profile.SalaryGrade = request.form.get("SalaryGrade")
        profile.PaymentMethod = request.form.get("PaymentMethod")

        db.session.commit()
        flash("✅ Đã cập nhật hồ sơ nhân sự.", "success")

        return redirect(url_for("hr.profile_detail", employee_id=employee_id))

    # --- GET: tính hệ số gần nhất để hiển thị ở tab Lương & phụ cấp ---
    latest = (
        HRSalaryHistory.query.filter_by(EmployeeID=employee_id)
        .order_by(HRSalaryHistory.EffectiveDate.desc(), HRSalaryHistory.SalaryID.desc())
        .first()
    )
    latest_coef = latest.Coefficient if latest else None
    latest_date = latest.EffectiveDate if latest else None

    return render_template(
        "hr/detail_edit.html",
        profile=profile,
        departments=departments,
        job_positions=job_positions,
        latest_coef=latest_coef,
        latest_date=latest_date,
    )


# Xoá hồ sơ
@hr_bp.route("/delete/<string:employee_id>", methods=["POST"])
@login_required
@check_permission("hr", "delete")
def delete_profile(employee_id):
    """
    Xoá hồ sơ nhân sự và dọn file ảnh nếu có.
    YÊU CẦU: Các FK ở SQL Server trỏ tới HRProfiles(EmployeeID) phải cấu hình ON DELETE CASCADE.
    """
    from sqlalchemy.exc import IntegrityError

    profile = HRProfile.query.get_or_404(employee_id)

    # Lưu đường dẫn ảnh hiện tại (nếu có) để dọn sau khi DB commit xong
    photo_to_remove = None
    if profile.Photo:
        # Photo lưu theo dạng "YYYY/MM/employeeid.ext"
        photo_rel = profile.Photo.replace("/", os.sep)
        photo_abs = os.path.join(UPLOAD_PHOTO_ROOT, photo_rel)
        photo_to_remove = photo_abs if os.path.exists(photo_abs) else None

    try:
        # Sử dụng transaction để đảm bảo tính nguyên tử
        db.session.delete(profile)
        db.session.flush()  # Đẩy lệnh xuống DB để kiểm tra ràng buộc ngay

        # Nếu tới đây không lỗi, tiến hành commit
        db.session.commit()

    except IntegrityError as e:
        db.session.rollback()
        # Trường hợp này thường do một FK chưa cấu hình CASCADE hoặc NO ACTION
        flash(
            "❌ Không thể xoá hồ sơ vì ràng buộc dữ liệu tham chiếu. "
            "Hãy kiểm tra các khoá ngoại chưa đặt ON DELETE CASCADE/SET NULL.",
            "danger",
        )
        # Gợi ý nhanh: ghi chi tiết lỗi vào log server cho admin
        # current_app.logger.exception(e)
        return redirect(url_for("hr.profile_detail", employee_id=employee_id))

    # Dọn ảnh sau khi commit thành công (tránh xoá nhầm nếu DB rollback)
    if photo_to_remove:
        try:
            os.remove(photo_to_remove)
        except Exception:
            # Không chặn luồng nếu lỗi xoá file; người dùng vẫn thấy xoá hồ sơ thành công
            # current_app.logger.warning(f"Không xoá được file ảnh: {photo_to_remove}")
            pass

    flash("🗑️ Đã xoá hồ sơ nhân sự và dữ liệu liên quan.", "success")
    return redirect(url_for("hr.list_profiles"))


# --- IMPORT EXCEL HRProfiles (đầy đủ, có StaffCode) ---

from werkzeug.utils import secure_filename
import pandas as pd
import os


# routes/hr.py  --- THAY THẾ TOÀN BỘ HÀM NÀY ---
@hr_bp.route("/import_excel", methods=["GET", "POST"])
@login_required
@check_permission("hr", "create")
def import_excel_hr_profiles():
    from flask import current_app
    import pandas as pd
    from datetime import datetime
    import csv, os
    from sqlalchemy.orm import Session

    if request.method == "GET":
        return render_template("hr/import.html")

    file = request.files.get("file")
    if not file or file.filename.strip() == "":
        flash("Vui lòng chọn file Excel .xlsx", "error")
        return redirect(request.url)

    filename = secure_filename(file.filename)
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    # --- Đọc sheet có EmployeeID ---
    xls = pd.ExcelFile(filepath, engine="openpyxl")
    df = None
    for sheet in xls.sheet_names:
        t = pd.read_excel(xls, sheet_name=sheet, engine="openpyxl").dropna(how="all")
        if t.shape[1] == 0:
            continue
        t.columns = [str(c).strip() for c in t.columns]
        if "EmployeeID" not in t.columns:
            first_col = t.iloc[:, 0].astype(str).str.strip()
            hit = t.index[first_col.eq("EmployeeID")].tolist()
            if hit:
                header_row = hit[0]
                t2 = t.iloc[header_row:, :].copy()
                if t2.shape[0] > 0:
                    t2.columns = t2.iloc[0].astype(str).str.strip().tolist()
                    t = t2[1:].dropna(how="all")
        if "EmployeeID" in t.columns:
            df = t
            break

    if df is None:
        flash("Không tìm thấy sheet nào có cột 'EmployeeID'.", "error")
        return redirect(url_for("hr.import_excel_hr_profiles"))

    df.columns = [str(c).strip() for c in df.columns]
    for col in ["STT", "#", "Index"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    # --- Map tên cột Excel -> field Model ---
    FIELD_MAP = {
        "EmployeeID": ["EmployeeID"],
        "StaffCode": ["StaffCode"],
        "FullName": ["FullName"],
        "Gender": ["Gender"],
        "DateOfBirth": ["DateOfBirth", "BirthDate"],
        "Nationality": ["Nationality"],
        "Ethnicity": ["Ethnicity"],
        "IDNumber": ["IDNumber"],
        "IDIssuedDate": ["IDIssuedDate", "IDIssueDate"],
        "IDIssuedPlace": ["IDIssuedPlace", "IDIssuePlace"],
        "DepartmentCode": ["DepartmentCode"],
        # Lưu ý: Excel có thể để mã 'TP/NV' ở cột JobPositionID
        "JobPositionID": [
            "JobPositionID",
            "JobPositionCode",
            "PositionCode",
            "JobPositionName",
            "JobTitle",
            "JobTitleCode",
        ],
        "ResidenceAddress": ["ResidenceAddress", "Address"],
        "Email": ["Email"],
        "Phone": ["Phone"],
        "InsuranceNumber": ["InsuranceNumber", "BHXHNumber"],
        "InsuranceIssuedDate": ["InsuranceIssuedDate", "BHXHIssueDate"],
        "TaxCode": ["TaxCode", "TaxNumber"],
        "TaxIssuedDate": ["TaxIssuedDate"],
        "TechnicalLevel": ["TechnicalLevel", "Degree"],
        "StartDate": ["StartDate", "StartWorkingDate"],
        "ContractNumber": ["ContractNumber"],
        "ContractType": ["ContractType"],
        "Salary": ["Salary"],
        "Notes": ["Notes"],
    }
    DATE_FIELDS = {"DateOfBirth", "IDIssuedDate", "InsuranceIssuedDate", "TaxIssuedDate", "StartDate"}

    def to_dt(val):
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return None
        if isinstance(val, (pd.Timestamp, datetime)):
            return pd.to_datetime(val)
        if isinstance(val, (int, float)):
            try:
                return pd.to_datetime(val, origin="1899-12-30", unit="D")
            except Exception:
                return None
        s = str(val).strip()
        dt = pd.to_datetime(s, errors="coerce", dayfirst=False)
        if pd.isna(dt):
            dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
        return None if pd.isna(dt) else dt

    # --- Lập bảng tra JobPosition: mã → ID (dò nhiều kiểu cột) ---
    jobpos_code_to_id = {}
    jobpos_name_to_id = {}
    id_attr = None
    with db.session.no_autoflush:
        for jp in JobPosition.query.all():
            # đoán tên cột ID
            for cand in ["JobPositionID", "PositionID", "Id", "ID"]:
                if hasattr(jp, cand):
                    id_attr = cand
                    break
            jp_id = getattr(jp, id_attr) if id_attr else None
            # các cột mã/tên có thể có
            for code_col in ["Code", "PositionCode", "JobPositionCode", "Abbrev", "ShortName"]:
                if hasattr(jp, code_col):
                    val = getattr(jp, code_col)
                    if val:
                        jobpos_code_to_id[str(val).strip().upper()] = jp_id
            for name_col in ["Name", "JobPositionName", "Title", "JobTitle"]:
                if hasattr(jp, name_col):
                    val = getattr(jp, name_col)
                    if val:
                        jobpos_name_to_id[str(val).strip().upper()] = jp_id

    def resolve_jobposition_id(raw):
        """Trả về int ID; nhận số hoặc mã/tên."""
        if raw is None:
            return None
        s = str(raw).strip()
        if s.isdigit():
            return int(s)
        key = s.upper()
        if key in jobpos_code_to_id:
            return jobpos_code_to_id[key]
        if key in jobpos_name_to_id:
            return jobpos_name_to_id[key]
        return None  # không tra được

    # --- Chỉ gán field có thật trong model ---
    model_fields = {c.key for c in HRProfile.__table__.columns}

    success, updated, failed = 0, 0, 0
    errors_path = os.path.join(upload_folder, "import_errors.csv")
    error_rows = []

    # Lặp từng dòng
    for idx, s in df.iterrows():
        row = s.to_dict()

        # ghép payload
        payload = {}
        for model_field, excel_keys in FIELD_MAP.items():
            val = None
            for k in excel_keys:
                if k in row and pd.notna(row[k]):
                    val = row[k]
                    break
            if model_field in DATE_FIELDS:
                val = to_dt(val)
            payload[model_field] = val

        # xử lý đặc biệt JobPositionID
        payload["JobPositionID"] = resolve_jobposition_id(payload.get("JobPositionID"))

        emp = str(payload.get("EmployeeID") or "").strip()
        if not emp:
            failed += 1
            error_rows.append({"row": int(idx) + 2, "EmployeeID": "", "error": "Thiếu EmployeeID"})
            continue

        try:
            # tránh autoflush pending rows trước khi query
            with db.session.no_autoflush:
                prof = HRProfile.query.filter_by(EmployeeID=emp).first()

            clean = {k: v for k, v in payload.items() if k in model_fields}

            # Nếu DB yêu cầu JobPositionID là NOT NULL mà không tra được → báo lỗi
            if "JobPositionID" in model_fields and clean.get("JobPositionID") is None:
                failed += 1
                error_rows.append(
                    {"row": int(idx) + 2, "EmployeeID": emp, "error": "Không tra được JobPositionID từ mã/tên"}
                )
                continue

            if prof:
                for k, v in clean.items():
                    if k == "EmployeeID":
                        continue
                    setattr(prof, k, v)
                # flush từng dòng để bắt lỗi kiểu dữ liệu/nghiệp vụ sớm
                db.session.flush()
                updated += 1
            else:
                new_prof = HRProfile(**clean)
                db.session.add(new_prof)
                db.session.flush()
                success += 1

        except Exception as e:
            db.session.rollback()  # rollback lỗi của dòng hiện tại
            failed += 1
            error_rows.append({"row": int(idx) + 2, "EmployeeID": emp, "error": repr(e)})

    # Commit cuối
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        error_rows.append({"row": "COMMIT", "EmployeeID": "", "error": repr(e)})
        flash(f"Lỗi commit CSDL: {e}", "error")

    if error_rows:
        with open(errors_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["row", "EmployeeID", "error"])
            w.writeheader()
            w.writerows(error_rows)
        flash(f"Có {len(error_rows)} dòng lỗi. Xem chi tiết: {errors_path}", "warning")

    flash(f"Import hoàn tất: {success} thêm mới, {updated} cập nhật, {failed} lỗi.", "success")
    return redirect(url_for("hr.import_excel_hr_profiles"))
