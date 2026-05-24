# routes/procurement.py
from __future__ import annotations
import os, csv, math, unicodedata
from io import BytesIO
from typing import Dict, List, Set, Tuple
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, or_, cast, Integer, Unicode, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.utils import secure_filename

from extensions import db
from models.procurement.tender_package_model import TenderPackage
from models.procurement.group_models import TenderExpertMember, TenderAppraisalMember
from models.hr.hr_profiles import HRProfile

from models.hr.employee_model import Employee
from utils.permission_utils import check_permission


procurement_bp = Blueprint("procurement", __name__, url_prefix="/procurement")

# ===================== Normalize helpers =====================
_SQL_COLLATION = "utf8mb4_general_ci" if os.environ.get("DB_TYPE") == "mysql" else "Latin1_General_100_CI_AI"


def _nfc(s: str) -> str:
    try:
        return unicodedata.normalize("NFC", s)
    except Exception:
        return s


def _norm(s) -> str:
    """Trim + bỏ NBSP + NFC + UPPER."""
    s = _nfc(str(s or "").replace("\u00a0", "").strip())
    return s.upper()


def _norm_pkg(s) -> str:
    """Trim + bỏ NBSP + NFC (GIỮ nguyên hoa/thường để hiển thị)."""
    return _nfc(str(s or "").replace("\u00a0", "").strip())


def _fix_mojibake(s: str) -> str:
    """Sửa chuỗi lỗi mã hoá kiểu Ð/ð hoặc Ã..."""
    if s is None:
        return ""
    s = str(s)
    if ("Ð" not in s) and ("Ã" not in s) and ("ð" not in s):
        return s
    try:
        r = s.encode("latin1").decode("utf-8")
        if r and r != s:
            return r
    except Exception:
        pass
    return s.replace("Ð", "Đ").replace("ð", "đ")


def _canon_empid(s) -> str:
    """Chuẩn hoá mã nhân sự để so sánh/ghi log ổn định.

    Mục tiêu: tránh phát sinh log thừa và lệch hiển thị do ký tự Đ/Ð (mojibake).
    - Sửa mojibake (Ð/ð, Ã...)
    - Quy về Đ/đ
    - Trim + NFC + UPPER
    """
    s = _fix_mojibake(str(s or ""))
    s = s.replace("Ð", "Đ").replace("ð", "đ")
    return _norm(s)


def _canon_pkg(s) -> str:
    """Chuẩn hoá PackageCode để match bền vững (Đ/Ð, mojibake, NFC)."""
    s = _fix_mojibake(_norm_pkg(s))
    s = (s or "").replace("Ð", "Đ").replace("ð", "đ")
    return _nfc(s)


def _pkg_code_variants(s) -> List[str]:
    """Sinh biến thể PackageCode để query (Đ/Ð, mojibake, latin1-decode)."""
    base = _norm_pkg(s)
    fixed = _fix_mojibake(base)
    canon = _canon_pkg(base)
    out: Set[str] = set()

    def add(x: str):
        x = _norm_pkg(x)
        if x:
            out.add(x)

    add(base)
    add(fixed)
    add(canon)
    add(base.replace("Đ", "Ð").replace("đ", "ð"))
    add(fixed.replace("Đ", "Ð").replace("đ", "ð"))
    add(canon.replace("Đ", "Ð").replace("đ", "ð"))
    try:
        add(base.encode("utf-8").decode("latin1"))
    except Exception:
        pass
    try:
        add(fixed.encode("utf-8").decode("latin1"))
    except Exception:
        pass
    return list(out)


def _sql_norm(col):
    c = cast(col, Unicode()).collate(_SQL_COLLATION)
    return func.upper(func.replace(func.ltrim(func.rtrim(c)), func.char(160), ""))


def _sql_norm_pkg(col):
    c = cast(col, Unicode()).collate(_SQL_COLLATION)
    return func.replace(func.ltrim(func.rtrim(c)), func.char(160), "")


def _variants(raw) -> List[str]:
    """Sinh nhiều biến thể key để match EmployeeID/StaffCode/Username/numeric."""
    if raw is None:
        return []
    raw_s = str(raw).strip()
    rep = _fix_mojibake(raw_s)
    bases = [raw_s] + ([rep] if rep and rep != raw_s else [])
    out, seen = [], set()
    for b in bases:
        nk = _norm(b)
        if not nk:
            continue
        cands = [nk]
        if "\\" in nk:
            cands.append(nk.split("\\")[-1])
        if "@" in nk:
            cands.append(nk.split("@")[0])
        if nk.isdigit():
            cands.append(nk.lstrip("0") or "0")
        for v in cands:
            v = (v or "").strip()
            if v and v not in seen:
                seen.add(v)
                out.append(v)
    return out


# ===================== HR helpers =====================
def _split_numeric(keys: Set[str]) -> List[int]:
    nums: List[int] = []
    for k in keys:
        try:
            if str(k).isdigit():
                nums.append(int(k))
        except Exception:
            pass
    return nums


def _load_hr_maps(keys: Set[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Trả (name_map, empid_map) cho các key variants."""
    if not keys:
        return {}, {}
    keys_list = list(keys)
    nums = _split_numeric(keys)

    conds = [
        _sql_norm(HRProfile.EmployeeID).in_(keys_list),
        _sql_norm(HRProfile.StaffCode).in_(keys_list),
    ]
    if nums:
        conds += [
            func.try_convert(Integer, HRProfile.EmployeeID).in_(nums),
            func.try_convert(Integer, HRProfile.StaffCode).in_(nums),
        ]

    rows = db.session.query(HRProfile.EmployeeID, HRProfile.StaffCode, HRProfile.FullName).filter(or_(*conds)).all()

    name_map: Dict[str, str] = {}
    empid_map: Dict[str, str] = {}

    def put(k, emp_norm: str, full: str):
        for v in _variants(k):
            empid_map[v] = emp_norm
            if full:
                name_map[v] = full

    for empid, staff, fullname in rows:
        emp_norm = _norm(empid)
        full = (fullname or "").strip()
        if emp_norm:
            put(empid, emp_norm, full)
            put(staff, emp_norm, full)

    # Username -> EmployeeID (+ FullName)
    if Employee is not None and hasattr(Employee, "Username") and hasattr(Employee, "EmployeeID"):
        try:
            emp_rows = (
                db.session.query(Employee.Username, Employee.EmployeeID)
                .filter(_sql_norm(Employee.Username).in_(keys_list))
                .all()
            )
            empids = [(_norm(eid)) for _, eid in emp_rows if eid]
            empids = [e for e in empids if e]

            empid2name = {}
            if empids:
                hr_rows = (
                    db.session.query(HRProfile.EmployeeID, HRProfile.FullName)
                    .filter(_sql_norm(HRProfile.EmployeeID).in_(empids))
                    .all()
                )
                empid2name = {_norm(eid): (fn or "").strip() for eid, fn in hr_rows if fn}

            for uname, eid in emp_rows:
                emp_norm = _norm(eid)
                if not emp_norm:
                    continue
                full = empid2name.get(emp_norm, "")
                put(uname, emp_norm, full)

        except Exception:
            pass

    return name_map, empid_map


def _resolve_hr_employeeids(keys_raw: List[str]) -> Set[str]:
    allk: Set[str] = set()
    for k in keys_raw:
        allk.update(_variants(k))
    name_map, empid_map = _load_hr_maps(allk)
    _ = name_map  # unused here
    out: Set[str] = set()
    for k in allk:
        eid = empid_map.get(k)
        if eid:
            out.add(eid)
    return out


def _collect_delete_keys(empids_norm: List[str]) -> Set[str]:
    """Gom key để xử lý xung đột (eid/staff/username/variants)."""
    if not empids_norm:
        return set()

    keys: Set[str] = set()
    for eid in empids_norm:
        keys.update(_variants(eid))

    hr_rows = (
        db.session.query(HRProfile.EmployeeID, HRProfile.StaffCode)
        .filter(_sql_norm(HRProfile.EmployeeID).in_(empids_norm))
        .all()
    )
    for empid, staff in hr_rows:
        keys.update(_variants(empid))
        keys.update(_variants(staff))

    if Employee is not None and hasattr(Employee, "EmployeeID") and hasattr(Employee, "Username"):
        try:
            e_rows = (
                db.session.query(Employee.EmployeeID, Employee.Username)
                .filter(_sql_norm(Employee.EmployeeID).in_(empids_norm))
                .all()
            )
            for _, uname in e_rows:
                keys.update(_variants(uname))
        except Exception:
            pass

    return {k for k in keys if k}


# --- (giữ lại để tham chiếu, KHÔNG còn dùng) ---
def _delete_conflicts_global(delete_keys: Set[str]):
    """
    ❌ Deprecated: Xoá xung đột TOÀN HỆ THỐNG theo EmployeeID (gây lỗi xoá người ở gói khác).
    Hiện tại không còn được gọi nữa để đảm bảo 1 người có thể ở nhiều gói.
    """
    if not delete_keys:
        return
    kl = list(delete_keys)
    TenderExpertMember.query.filter(_sql_norm(TenderExpertMember.EmployeeID).in_(kl)).delete(synchronize_session=False)
    TenderAppraisalMember.query.filter(_sql_norm(TenderAppraisalMember.EmployeeID).in_(kl)).delete(
        synchronize_session=False
    )


# ✅ NEW: chỉ xoá xung đột TRONG CÙNG GÓI THẦU
def _delete_conflicts_in_package(package_code: str, other_model, delete_keys: Set[str]):
    """
    Chỉ xoá xung đột trong CÙNG 1 gói thầu:
    - Khi lưu tổ A (this_model) cho gói X, sẽ xoá các thành viên đó khỏi tổ B (other_model) của CHÍNH gói X.
    - KHÔNG đụng tới các gói thầu khác.
    """
    if not package_code or not delete_keys:
        return
    pkg_vars = _pkg_code_variants(package_code)
    kl = list(delete_keys)
    other_model.query.filter(
        or_(
            other_model.PackageCode.in_(pkg_vars),
            _sql_norm_pkg(other_model.PackageCode).in_(pkg_vars),
        )
    ).filter(_sql_norm(other_model.EmployeeID).in_(kl)).delete(synchronize_session=False)


# ===================== Dept helpers =====================
def _current_user_dept_norm() -> str:
    dept = getattr(current_user, "DepartmentCode", None) or getattr(current_user, "DeptCode", None)
    if dept:
        return _norm(dept)

    if Employee is None or not hasattr(Employee, "DepartmentCode"):
        return ""

    try:
        uname = getattr(current_user, "Username", None) or getattr(current_user, "username", None)
        eid = getattr(current_user, "EmployeeID", None) or getattr(current_user, "employee_id", None)
        conds = []
        if uname and hasattr(Employee, "Username"):
            conds.append(_sql_norm(Employee.Username) == _norm(uname))
        if eid and hasattr(Employee, "EmployeeID"):
            conds.append(_sql_norm(Employee.EmployeeID) == _norm(eid))
        if conds:
            dept2 = db.session.query(Employee.DepartmentCode).filter(or_(*conds)).scalar()
            return _norm(dept2) if dept2 else ""
    except Exception:
        pass

    return ""


# ===================== Build group maps (List page) =====================
def _build_group_maps(codes: List[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Map raw PackageCode -> chuỗi HTML: mỗi người 1 dòng (<br>)."""
    if not codes:
        return {}, {}

    raw_codes = [c for c in codes if c is not None]
    wanted = set(_canon_pkg(c) for c in raw_codes)

    qcodes: Set[str] = set()
    for c in raw_codes:
        qcodes.update(_pkg_code_variants(c))
    if not qcodes:
        return {}, {}

    qlist = list(qcodes)

    exp = (
        db.session.query(TenderExpertMember.PackageCode, TenderExpertMember.EmployeeID)
        .filter(
            or_(TenderExpertMember.PackageCode.in_(qlist), _sql_norm_pkg(TenderExpertMember.PackageCode).in_(qlist))
        )
        .all()
    )
    app = (
        db.session.query(TenderAppraisalMember.PackageCode, TenderAppraisalMember.EmployeeID)
        .filter(
            or_(
                TenderAppraisalMember.PackageCode.in_(qlist),
                _sql_norm_pkg(TenderAppraisalMember.PackageCode).in_(qlist),
            )
        )
        .all()
    )

    allk: Set[str] = set()
    for _, k in exp:
        allk.update(_variants(k))
    for _, k in app:
        allk.update(_variants(k))

    name_map, empid_map = _load_hr_maps(allk)

    def emp_norm(k) -> str:
        for v in _variants(k):
            eid = empid_map.get(v)
            if eid:
                return eid
        return _norm(k)

    def disp(k) -> str:
        for v in _variants(k):
            nm = name_map.get(v)
            if nm:
                return nm
        return _fix_mojibake(str(k)).strip()

    def join_unique(pairs: List[Tuple[str, str]]) -> str:
        seen: Set[str] = set()
        out: List[str] = []
        for eid, nm in pairs:
            if not eid or eid in seen:
                continue
            seen.add(eid)
            if nm:
                out.append(nm)
        return "<br>".join(out)

    ex_pairs: Dict[str, List[Tuple[str, str]]] = {}
    ap_pairs: Dict[str, List[Tuple[str, str]]] = {}

    for code, k in exp:
        ck = _canon_pkg(code)
        if ck in wanted:
            ex_pairs.setdefault(ck, []).append((emp_norm(k), disp(k)))
    for code, k in app:
        ck = _canon_pkg(code)
        if ck in wanted:
            ap_pairs.setdefault(ck, []).append((emp_norm(k), disp(k)))

    ex_join = {k: join_unique(v) for k, v in ex_pairs.items()}
    ap_join = {k: join_unique(v) for k, v in ap_pairs.items()}

    ex_out = {raw: ex_join.get(_canon_pkg(raw), "") for raw in raw_codes}
    ap_out = {raw: ap_join.get(_canon_pkg(raw), "") for raw in raw_codes}
    return ex_out, ap_out


# ===================== Search by member name (List search) =====================
def _search_terms(q: str) -> List[str]:
    q = (q or "").strip()
    if not q:
        return []
    terms: List[str] = []

    def add(x: str):
        x = (x or "").strip()
        if x and x not in terms:
            terms.append(x)

    add(q)
    fixed = _fix_mojibake(q)
    if fixed != q:
        add(fixed)
    add(q.replace("Đ", "Ð").replace("đ", "ð"))
    add(q.replace("Đ", "D").replace("đ", "d"))
    try:
        add(q.encode("utf-8").decode("latin1"))
    except Exception:
        pass
    return terms


def _pkgcodes_by_member_name(member_model, terms: List[str]):
    """Subquery package codes theo HRProfile.FullName (an toàn, không JOIN trực tiếp)."""
    if not terms:
        return db.session.query(cast("", Unicode()).label("pkg")).filter(False).subquery()

    likes = [f"%{_norm(t)}%" for t in terms if t]
    if not likes:
        return db.session.query(cast("", Unicode()).label("pkg")).filter(False).subquery()

    name_cond = or_(*[_sql_norm(HRProfile.FullName).like(lk) for lk in likes])
    hr_rows = db.session.query(HRProfile.EmployeeID, HRProfile.StaffCode).filter(name_cond).all()

    keys: Set[str] = set()
    empids_norm: Set[str] = set()
    for empid, staff in hr_rows:
        keys.update(_variants(empid))
        keys.update(_variants(staff))
        ne = _norm(empid)
        if ne:
            empids_norm.add(ne)

    if Employee is not None and hasattr(Employee, "EmployeeID") and hasattr(Employee, "Username") and empids_norm:
        try:
            e_rows = (
                db.session.query(Employee.EmployeeID, Employee.Username)
                .filter(_sql_norm(Employee.EmployeeID).in_(list(empids_norm)))
                .all()
            )
            for _, uname in e_rows:
                keys.update(_variants(uname))
        except Exception:
            pass

    keys_list = [k for k in keys if k]
    if not keys_list:
        return db.session.query(cast("", Unicode()).label("pkg")).filter(False).subquery()

    return (
        db.session.query(_sql_norm_pkg(member_model.PackageCode).label("pkg"))
        .filter(_sql_norm(member_model.EmployeeID).in_(keys_list))
        .distinct()
        .subquery()
    )


# ===================== Excel helpers =====================
def _xlsx_from_rows(headers, rows, sheet="TongHopGoiThau") -> BytesIO:
    """
    Export Excel - chuẩn theo yêu cầu:
    - Wrap text: cột B, E, F (B=2, E=5, F=6)
    - Row height: tự tính để hiển thị đủ nội dung (kể cả cột B dài không có '\n')
    - Alignment:
      + Cột A, B: căn trái
      + Cột D: căn phải
      + Cột còn lại: căn giữa
      Tất cả: căn giữa theo chiều dọc (vertical center).
    """
    wb = Workbook()
    ws = wb.active
    ws.title = (sheet or "Sheet1")[:31]

    LEFT_COLS = {1, 2}  # A, B
    RIGHT_COLS = {4}  # D
    WRAP_COLS = {2, 5, 6}  # B, E, F

    def _h_align(col_idx: int) -> str:
        if col_idx in LEFT_COLS:
            return "left"
        if col_idx in RIGHT_COLS:
            return "right"
        return "center"

    # 1) Header
    ws.append(list(headers))
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    header_font = Font(bold=True)
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal=_h_align(col), vertical="center", wrap_text=True)

    # 2) Data rows
    for r in rows:
        ws.append(list(r))

    ws.freeze_panes = "A2"

    # 3) Format số cột D
    for row_cells in ws.iter_rows(min_row=2, min_col=4, max_col=4):
        for cell in row_cells:
            if isinstance(cell.value, (int, float)) and cell.value is not None:
                cell.number_format = "#,##0"

    # 4) Auto width
    for col in range(1, len(headers) + 1):
        letter = get_column_letter(col)
        max_len = 10
        for cell in ws[letter]:
            if cell.value is None:
                continue
            s = str(cell.value)
            parts = s.splitlines() if ("\n" in s) or ("\r" in s) else [s]
            longest = max((len(p) for p in parts), default=0)
            if longest > max_len:
                max_len = longest
        ws.column_dimensions[letter].width = min(max_len + 2, 60)

    # 5) Row height theo wrap
    LINE_HEIGHT = 17
    PADDING = 2

    def _col_width_chars(col_letter: str) -> int:
        w = ws.column_dimensions[col_letter].width
        if w is None:
            return 8
        return max(1, int(float(w) - 1))

    def _estimate_wrapped_lines(text: str, width_chars: int) -> int:
        if not text:
            return 1
        lines = 0
        for part in str(text).splitlines():
            part = part.strip()
            if not part:
                lines += 1
                continue
            lines += max(1, int(math.ceil(len(part) / float(width_chars))))
        return max(lines, 1)

    wrap_col_letters = {idx: get_column_letter(idx) for idx in WRAP_COLS}
    for r_idx in range(2, ws.max_row + 1):
        max_lines = 1
        for c_idx in WRAP_COLS:
            cell = ws.cell(row=r_idx, column=c_idx)
            v = "" if cell.value is None else str(cell.value)
            width_chars = _col_width_chars(wrap_col_letters[c_idx])
            need_lines = _estimate_wrapped_lines(v, width_chars)
            if need_lines > max_lines:
                max_lines = need_lines
        ws.row_dimensions[r_idx].height = max(LINE_HEIGHT, max_lines * LINE_HEIGHT + PADDING)

    # 6) Alignment body
    for r_idx in range(2, ws.max_row + 1):
        for c_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.alignment = Alignment(horizontal=_h_align(c_idx), vertical="center", wrap_text=(c_idx in WRAP_COLS))

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio


def _send_xlsx(bio: BytesIO, filename: str):
    try:
        bio.seek(0)
    except Exception:
        pass
    try:
        return send_file(
            bio,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            max_age=0,
        )
    except TypeError:
        return send_file(
            bio,
            as_attachment=True,
            attachment_filename=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ===================== Pagination =====================
class SimplePagination:
    def __init__(self, items=None, page: int = 1, per_page: int = 50, total: int = 0):
        self.items = items or []
        self.page = int(page or 1)
        self.per_page = int(per_page or 50)
        self.total = int(total or 0)

    @property
    def pages(self) -> int:
        return max(1, int(math.ceil(self.total / float(self.per_page)))) if self.per_page else 1

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_num(self) -> int:
        return max(1, self.page - 1)

    @property
    def next_num(self) -> int:
        return min(self.pages, self.page + 1)

    def iter_pages(self, left_edge=2, left_current=2, right_current=2, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (self.page - left_current - 1 < num < self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


# ===================== Routes: logs =====================
@procurement_bp.route("/logs", methods=["GET"])
@login_required
@check_permission("procurement", "read")
def procurement_logs():
    """Hiển thị log thao tác tổ chuyên gia/tổ thẩm định (tối đa 500 dòng).

        Hiển thị mong muốn:
        - Người thao tác: FullName (HRProfile) nếu resolve được; riêng admin -> "Người quản trị".
        - Hành động/Phân hệ: tiếng Việt (ADD/DELETE -> Thêm/Xoá; ExpertGroup -> Tổ chuyên gia...).
        - Chi tiết: "<PackageCode>|| <FullName>" (hoặc fallback về mã NV nếu chưa map được).

        Ghi chú:
        - dbo.ProcurementActionLog.EmployeeID đang lưu *actor* (tài khoản thao tác) có thể là Username.
        - Description lưu bởi _pack_desc(): "<PackageCode>

    <EmployeeID>" (và có thể có log cũ dạng "||").
    """
    try:
        module = (request.args.get("module") or "").strip()
        action = (request.args.get("action") or "").strip()
        employee = (request.args.get("employee") or "").strip()

        rows = (
            db.session.execute(
                text("""
                SELECT
                    EmployeeID,
                    Action      AS Action,
                    Module      AS Module,
                    Description AS Description,
                    Timestamp   AS Timestamp
                FROM ProcurementActionLog
                WHERE Module IN ('ExpertGroup', 'AppraisalGroup')
                  AND (:module = '' OR Module = :module)
                  AND (:action = '' OR Action = :action)
                  AND (:employee = '' OR EmployeeID = :employee)
                ORDER BY Timestamp DESC
                LIMIT 500
            """),
                {"module": module, "action": action, "employee": employee},
            )
            .mappings()
            .all()
        )

        enriched = []
        pkg_set, target_emp_set, actor_set = set(), set(), set()

        for r in rows:
            pkg, target = _parse_desc(r.get("Description"))
            actor_raw = (r.get("EmployeeID") or "").strip()

            if pkg:
                pkg_set.add(_canon_pkg(pkg))
            if target:
                target_emp_set.add(_canon_empid(target))
            if actor_raw:
                actor_set.add(actor_raw)

            enriched.append(
                {
                    **dict(r),
                    "PackageCode": pkg,
                    "TargetEmpID": target,
                    "TargetFullName": "",
                    "PackageName": "",
                    "ActorCode": actor_raw,
                    "ActorFullName": "",
                    "ActionVN": "",
                    "ModuleVN": "",
                    "DetailVN": "",
                }
            )

        # Resolve tên nhân sự bị tác động
        target_name_map = {}
        if target_emp_set:
            keys = set()
            for e in target_emp_set:
                keys.update(_variants(e))
            name_map, _empid_map = _load_hr_maps(keys)

            def resolve_name(empid: str) -> str:
                for v in _variants(empid):
                    nm = name_map.get(v)
                    if nm:
                        return (nm or "").strip()
                return ""

            for e in target_emp_set:
                target_name_map[e] = resolve_name(e)

        # Resolve tên gói thầu
        pkg_name_map = {}
        if pkg_set:
            qcodes = set()
            for c in pkg_set:
                qcodes.update(_pkg_code_variants(c))
            qlist = list(qcodes) if qcodes else []
            pkgs = []
            if qlist:
                pkgs = TenderPackage.query.filter(
                    or_(
                        TenderPackage.PackageCode.in_(qlist),
                        _sql_norm_pkg(TenderPackage.PackageCode).in_(qlist),
                    )
                ).all()
            pkg_name_map = {_canon_pkg(p.PackageCode): (p.PackageName or "") for p in pkgs}

        # Resolve tên người thao tác
        actor_name_map = {}
        actor_code_map = {}
        if actor_set:
            keys = set()
            for a in actor_set:
                keys.update(_variants(a))
            name_map, empid_map = _load_hr_maps(keys)

            def resolve_actor(a_raw: str):
                a_norm = _norm(a_raw)
                if a_norm in {"ADMIN", "ADMINISTRATOR"}:
                    return "Người quản trị", a_raw

                emp_norm = ""
                full = ""
                for v in _variants(a_raw):
                    if not emp_norm:
                        emp_norm = empid_map.get(v, "") or emp_norm
                    if not full:
                        nm = name_map.get(v)
                        if nm:
                            full = (nm or "").strip()
                return full, (emp_norm or a_raw)

            for a in actor_set:
                full, code = resolve_actor(a)
                actor_name_map[a] = full
                actor_code_map[a] = code

        ACTION_VN = {
            "ADD": "Thêm",
            "DELETE": "Xoá",
            "REMOVE": "Xoá",
            "UPDATE": "Cập nhật",
            "EDIT": "Cập nhật",
        }
        MODULE_VN = {
            "ExpertGroup": "Tổ chuyên gia",
            "AppraisalGroup": "Tổ thẩm định",
        }

        for item in enriched:
            actor_raw = (item.get("EmployeeID") or "").strip()
            actor_full = actor_name_map.get(actor_raw, "")
            actor_code = actor_code_map.get(actor_raw, actor_raw)
            item["ActorFullName"] = _fix_mojibake(actor_full).strip() if actor_full else ""
            item["ActorCode"] = _fix_mojibake(actor_code).strip() if actor_code else actor_raw

            target_emp = _canon_empid(item.get("TargetEmpID") or "")
            target_full = target_name_map.get(target_emp, "") if target_emp else ""
            item["TargetFullName"] = _fix_mojibake(target_full).strip() if target_full else ""

            pcode = _canon_pkg(item.get("PackageCode") or "")
            item["PackageName"] = pkg_name_map.get(pcode, "") if pcode else ""

            act = (item.get("Action") or "").strip().upper()
            mod = (item.get("Module") or "").strip()
            item["ActionVN"] = ACTION_VN.get(act, act or "")
            item["ModuleVN"] = MODULE_VN.get(mod, mod or "")

            pkg = (item.get("PackageCode") or "").strip()
            target_disp = item["TargetFullName"] or (item.get("TargetEmpID") or "").strip()
            pkg_disp = _fix_mojibake(pkg).strip()
            target_disp = _fix_mojibake(target_disp).strip()
            if pkg_disp and target_disp:
                item["DetailVN"] = f"{pkg_disp}|| {target_disp}"
            else:
                item["DetailVN"] = _fix_mojibake((item.get("Description") or "").strip())

        return render_template("logs.html", logs=enriched)

    except Exception as e:
        try:
            current_app.logger.exception("Load procurement logs failed")
        except Exception:
            pass
        flash(f"❌ Không tải được nhật ký: {e}", "danger")
        return redirect(url_for("procurement.list_packages"))


# ===================== Routes: list =====================
@procurement_bp.route("/", methods=["GET"])
@login_required
@check_permission("procurement", "read")
def list_packages():
    search = (request.args.get("search") or "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = 50 if per_page <= 0 else min(per_page, 200)
    page = 1 if page <= 0 else page

    try:
        q = TenderPackage.query
        if search:
            terms = _search_terms(search)
            likes = [f"%{_norm(t)}%" for t in terms if t]
            base = []
            for lk in likes:
                base += [
                    _sql_norm(TenderPackage.PackageCode).like(lk),
                    _sql_norm(TenderPackage.PackageName).like(lk),
                    _sql_norm(TenderPackage.PackageType).like(lk),
                ]
            base_cond = or_(*base) if base else None

            exp_sub = _pkgcodes_by_member_name(TenderExpertMember, terms)
            app_sub = _pkgcodes_by_member_name(TenderAppraisalMember, terms)
            pkg_union = (
                db.session.query(exp_sub.c.pkg.label("pkg"))
                .union(db.session.query(app_sub.c.pkg.label("pkg")))
                .subquery()
            )
            group_cond = _sql_norm_pkg(TenderPackage.PackageCode).in_(db.session.query(pkg_union.c.pkg))
            conds = [group_cond] + ([base_cond] if base_cond is not None else [])
            q = q.filter(or_(*conds))

        q = q.order_by(TenderPackage.PackageCode.asc())
        total = q.count()
        pages = max(1, int(math.ceil(total / float(per_page)))) if per_page else 1
        page = min(page, pages)
        items = q.offset((page - 1) * per_page).limit(per_page).all()

        codes = [p.PackageCode for p in items]
        expert_map, appraisal_map = _build_group_maps(codes)

        return render_template(
            "procurement_list.html",
            packages=SimplePagination(items, page=page, per_page=per_page, total=total),
            search=search,
            expert_map=expert_map,
            appraisal_map=appraisal_map,
            db_error=None,
        )

    except SQLAlchemyError as e:
        msg = "Không truy vấn được dữ liệu gói thầu. " + f"Chi tiết: {str(e).splitlines()[0]}"
        flash(msg, "warning")
        return render_template(
            "procurement_list.html",
            packages=SimplePagination([], page=1, per_page=per_page, total=0),
            search=search,
            expert_map={},
            appraisal_map={},
            db_error=msg,
        )


# ===================== Download / Export =====================
@procurement_bp.route("/download-excel", methods=["GET"])
@login_required
@check_permission("procurement", "read")
def download_excel():
    try:
        all_pkgs = TenderPackage.query.order_by(TenderPackage.PackageCode.asc()).all()
        codes = [p.PackageCode for p in all_pkgs]
        expert_map, appraisal_map = _build_group_maps(codes)

        headers = [
            "Mã hiệu gói thầu",
            "Tên gói thầu",
            "Loại",
            "Giá trị theo kế hoạch (Triệu đồng)",
            "Tổ chuyên gia",
            "Tổ thẩm định",
        ]

        rows = []
        for p in all_pkgs:
            rows.append(
                [
                    p.PackageCode,
                    p.PackageName,
                    p.PackageType or "",
                    float(p.PlanValue) if p.PlanValue is not None else None,
                    expert_map.get(p.PackageCode, "").replace("<br>", "\n"),
                    appraisal_map.get(p.PackageCode, "").replace("<br>", "\n"),
                ]
            )

        bio = _xlsx_from_rows(headers, rows, sheet="TongHopGoiThau")
        return _send_xlsx(bio, "tong_hop_goi_thau.xlsx")
    except Exception as e:
        flash(f"❌ Lỗi xuất Excel: {e}", "danger")
        return redirect(url_for("procurement.list_packages"))


@procurement_bp.route("/download-template", methods=["GET"])
@login_required
def download_template():
    return download_excel()


# ===================== Import Excel =====================
@procurement_bp.route("/import_excel", methods=["GET", "POST"])
@login_required
@check_permission("procurement", "create")
def import_excel_tender_packages():
    if request.method == "GET":
        return render_template("procurement_import.html")

    file = request.files.get("file")
    if not file or not file.filename.strip():
        flash("Vui lòng chọn file Excel .xlsx", "error")
        return redirect(request.url)

    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, secure_filename(file.filename))
    file.save(filepath)

    try:
        xls = pd.ExcelFile(filepath, engine="openpyxl")
    except Exception as e:
        flash(f"Lỗi đọc Excel: {e}", "error")
        return redirect(url_for("procurement.import_excel_tender_packages"))

    df = None
    for sh in xls.sheet_names:
        t = pd.read_excel(xls, sheet_name=sh, engine="openpyxl").dropna(how="all")
        if t.shape[1] == 0:
            continue
        t.columns = [str(c).strip() for c in t.columns]
        if "PackageCode" not in t.columns:
            first = t.iloc[:, 0].astype(str).str.strip()
            hit = t.index[first.eq("PackageCode")].tolist()
            if hit:
                h = hit[0]
                t2 = t.iloc[h:, :].copy()
                if t2.shape[0] > 0:
                    t2.columns = t2.iloc[0].astype(str).str.strip().tolist()
                    t = t2[1:].dropna(how="all")
        if "PackageCode" in t.columns:
            df = t
            break

    if df is None:
        flash("Không tìm thấy sheet nào có cột 'PackageCode'. Hãy dùng form mẫu.", "error")
        return redirect(url_for("procurement.import_excel_tender_packages"))

    df.columns = [str(c).strip() for c in df.columns]
    fmap = {
        "PackageCode": ["PackageCode", "Mã hiệu gói thầu", "Ma hieu goi thau", "MaGoiThau"],
        "PackageName": ["PackageName", "Tên gói thầu", "Ten goi thau", "TenGoiThau"],
        "PackageType": ["PackageType", "Loại", "Loai"],
        "PlanValue": ["PlanValue", "Giá trị theo kế hoạch", "Gia tri theo ke hoach", "GiaTriKeHoach"],
    }

    def pick(r, keys):
        for k in keys:
            if k in r and pd.notna(r[k]):
                return r[k]
        return None

    def money(v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        try:
            if isinstance(v, str):
                v = v.replace(",", "").strip()
            return float(v)
        except Exception:
            return None

    success = updated = failed = 0
    errs = []
    fields = {c.key for c in TenderPackage.__table__.columns}

    for idx, s in df.iterrows():
        r = s.to_dict()
        payload = {f: pick(r, ks) for f, ks in fmap.items()}
        code = str(payload.get("PackageCode") or "").strip()
        name = str(payload.get("PackageName") or "").strip()

        if not code:
            failed += 1
            errs.append({"row": int(idx) + 2, "PackageCode": "", "error": "Thiếu PackageCode"})
            continue
        if not name:
            failed += 1
            errs.append({"row": int(idx) + 2, "PackageCode": code, "error": "Thiếu PackageName"})
            continue

        payload["PlanValue"] = money(payload.get("PlanValue"))
        clean = {k: v for k, v in payload.items() if k in fields}

        try:
            obj = TenderPackage.query.filter_by(PackageCode=code).first()
            if obj:
                for k, v in clean.items():
                    if k != "PackageCode":
                        setattr(obj, k, v)
                db.session.flush()
                updated += 1
            else:
                db.session.add(TenderPackage(**clean))
                db.session.flush()
                success += 1
        except Exception as e:
            db.session.rollback()
            failed += 1
            errs.append({"row": int(idx) + 2, "PackageCode": code, "error": repr(e)})

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi commit CSDL: {e}", "error")
        return redirect(url_for("procurement.import_excel_tender_packages"))

    if errs:
        p = os.path.join(upload_folder, "tender_import_errors.csv")
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["row", "PackageCode", "error"])
            w.writeheader()
            w.writerows(errs)
        flash(f"Có {len(errs)} dòng lỗi. Xem: {p}", "warning")

    flash(f"Import hoàn tất: {success} thêm mới, {updated} cập nhật, {failed} lỗi.", "success")
    return redirect(url_for("procurement.list_packages"))


# ===================== Audit log helpers (ProcurementActionLog) =====================


def _actor_account() -> str:
    """Lấy tài khoản thao tác để ghi log (ưu tiên Username -> EmployeeID -> get_id())."""
    try:
        u = getattr(current_user, "Username", None) or getattr(current_user, "username", None)
        if u:
            return str(u).strip()
        eid = getattr(current_user, "EmployeeID", None) or getattr(current_user, "employee_id", None)
        if eid:
            return str(eid).strip()
        gid = current_user.get_id() if hasattr(current_user, "get_id") else ""
        return str(gid or "UNKNOWN").strip()
    except Exception:
        return "UNKNOWN"


def _group_module_name(model) -> str:
    """Gán Module chỉ còn 2 giá trị: ExpertGroup / AppraisalGroup."""
    try:
        name = getattr(model, "__name__", "") or str(model)
        if "TenderExpertMember" in name:
            return "ExpertGroup"
        if "TenderAppraisalMember" in name:
            return "AppraisalGroup"
    except Exception:
        pass
    return "Procurement"


def _pack_desc(package_code: str, target_empid: str) -> str:
    """Đóng gói Description để lưu được cả gói thầu + nhân sự.

    Format: <PackageCode>||<EmployeeID>
    - Dễ parse khi hiển thị log.
    - Tương thích ngược: log cũ chỉ có EmployeeID thì coi như không có PackageCode.
    """
    pkg = (_canon_pkg(package_code) if package_code else "").strip()
    eid = (_canon_empid(target_empid) if target_empid else "").strip()
    if pkg and eid:
        return f"{pkg}||{eid}"
    return (pkg or eid or "").strip()


def _parse_desc(desc: str):
    """Parse Description về (PackageCode, EmployeeID).

    Hỗ trợ nhiều định dạng để tương thích ngược:
    - Mới (khuyến nghị): "<PackageCode>\n\n<EmployeeID>"  (do _pack_desc tạo)
    - Cũ: "<PackageCode>||<EmployeeID>" hoặc "<PackageCode>|| <EmployeeID>"
    - Rất cũ: chỉ có "<EmployeeID>" (không có PackageCode)
    """
    s = (desc or "").strip()
    if not s:
        return "", ""

    # ✅ Định dạng mới
    if "\n\n" in s:
        a, b = s.split("\n\n", 1)
        return (a or "").strip(), (b or "").strip()

    # ✅ Định dạng cũ dùng '||'
    if "||" in s:
        a, b = s.split("||", 1)
        return (a or "").strip(), (b or "").strip()

    # ✅ Rất cũ: chỉ có EmployeeID
    return "", s


def _write_procurement_log(actor: str, action: str, module: str, package_code: str, target_empid: str):
    """Ghi 1 bản ghi vào dbo.ProcurementActionLog."""
    db.session.execute(
        text("""
            INSERT INTO ProcurementActionLog (EmployeeID, Action, Module, Description, Timestamp)
            VALUES (:actor, :action, :module, :desc, NOW())
        """),
        {
            "actor": (actor or "UNKNOWN").strip(),
            "action": (action or "").strip(),
            "module": (module or "Procurement").strip(),
            "desc": _pack_desc(package_code, target_empid),
        },
    )


# ===================== Group pages (save + conflict) =====================
def _members_norm() -> List[str]:
    seen, out = set(), []
    for x in request.form.getlist("members"):
        nx = _canon_empid(x)
        if nx and nx not in seen:
            seen.add(nx)
            out.append(nx)
    return out


def _save_group(package_code: str, model_this, other_model, members: List[str], ok_msg: str) -> bool:
    """
    Lưu nhóm cho 1 gói:
    - Chỉ xoá xung đột (khóa chéo) trong CÙNG gói.
    - Không xoá người đó ở các gói khác => 1 người có thể tham gia nhiều gói.

    Ghi log vào dbo.ProcurementActionLog:
    - Tài khoản thao tác (actor)
    - Gói thầu (PackageCode)
    - Nhân sự thay đổi (EmployeeID)
    - Hành động: ADD hoặc DELETE
    - Thời điểm (GETDATE())

    Lưu ý: màn hình lưu theo kiểu "xoá hết rồi insert lại".
    Vì vậy để ra log thêm/xoá đúng nghĩa, cần so sánh danh sách trước/sau.
    """
    package_code = _canon_pkg(package_code)
    if not package_code:
        flash("Vui lòng chọn gói thầu.", "warning")
        return False

    try:
        # rollback transaction cũ nếu có
        try:
            if db.session.in_transaction():
                db.session.rollback()
        except Exception:
            pass

        pkg_vars = _pkg_code_variants(package_code)

        # 1) Lấy danh sách cũ (trong đúng gói) để tính diff
        old_this_raw = [
            r.EmployeeID
            for r in model_this.query.filter(
                or_(
                    model_this.PackageCode.in_(pkg_vars),
                    _sql_norm_pkg(model_this.PackageCode).in_(pkg_vars),
                )
            ).all()
        ]
        old_other_raw = [
            r.EmployeeID
            for r in other_model.query.filter(
                or_(
                    other_model.PackageCode.in_(pkg_vars),
                    _sql_norm_pkg(other_model.PackageCode).in_(pkg_vars),
                )
            ).all()
        ]

        old_this = {_canon_empid(x) for x in old_this_raw if _canon_empid(x)}
        old_other = {_canon_empid(x) for x in old_other_raw if _canon_empid(x)}
        new_set = {_canon_empid(x) for x in (members or []) if _canon_empid(x)}

        added = sorted(list(new_set - old_this))
        removed = sorted(list(old_this - new_set))

        # Nhân sự bị xoá khỏi tổ còn lại do "khóa chéo" trong CÙNG gói
        conflict_removed = sorted(list(old_other.intersection(new_set)))

        # 2) Xoá xung đột trong cùng gói (other_model)
        delete_keys = _collect_delete_keys(list(new_set))
        _delete_conflicts_in_package(package_code, other_model, delete_keys)

        # 3) Xoá danh sách cũ của model_this trong gói và insert danh sách mới
        model_this.query.filter(
            or_(
                model_this.PackageCode.in_(pkg_vars),
                _sql_norm_pkg(model_this.PackageCode).in_(pkg_vars),
            )
        ).delete(synchronize_session=False)

        for empid in sorted(list(new_set)):
            db.session.add(model_this(PackageCode=package_code, EmployeeID=empid))

        # 4) Ghi log
        actor = _actor_account()
        module_this = _group_module_name(model_this)
        module_other = _group_module_name(other_model)

        for eid in added:
            _write_procurement_log(actor, "ADD", module_this, package_code, eid)

        for eid in removed:
            _write_procurement_log(actor, "DELETE", module_this, package_code, eid)

        for eid in conflict_removed:
            _write_procurement_log(actor, "DELETE", module_other, package_code, eid)

        db.session.commit()
        flash(ok_msg, "success")
        return True

    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.exception("IntegrityError save group pkg=%s", package_code)
        flash(f"❌ Conflict/Unique: {e}", "danger")
        return False
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error save group pkg=%s", package_code)
        flash(f"❌ Lỗi lưu: {e}", "danger")
        return False


def _merge_employees(pinned: List[HRProfile], main: List[HRProfile], pinned_checked: Set[str], pinned_locked: Set[str]):
    """Đưa pinned lên đầu, khử trùng theo EmployeeID."""

    def key(e: HRProfile):
        eid = _norm(getattr(e, "EmployeeID", ""))
        tier = 2
        if eid in pinned_checked:
            tier = 0
        elif eid in pinned_locked:
            tier = 1
        return (tier, (getattr(e, "FullName", "") or "").lower())

    out, seen = [], set()
    for e in sorted(pinned, key=key) + main:
        eid = _norm(getattr(e, "EmployeeID", ""))
        if eid and eid not in seen:
            seen.add(eid)
            out.append(e)

    if pinned_checked or pinned_locked:
        out.sort(key=key)
    return out


def _group_page(template: str, this_model, other_model, ok_msg: str, filter_by_dept: bool = True):
    packages = TenderPackage.query.order_by(TenderPackage.PackageCode.asc()).all()
    pkg = _norm_pkg(request.form.get("package_code") or request.args.get("package_code") or "")
    search = (request.form.get("search") or request.args.get("search") or "").strip()

    emp_q = HRProfile.query
    if filter_by_dept:
        dept_norm = _current_user_dept_norm()
        if dept_norm and hasattr(HRProfile, "DepartmentCode"):
            emp_q = emp_q.filter(_sql_norm(HRProfile.DepartmentCode) == dept_norm)

    # pinned: đã chọn + bị khoá (khoá chéo trong cùng gói)
    preselected_norm, locked_norm = set(), set()
    if pkg:
        pkg_vars = _pkg_code_variants(pkg)
        this_raw = [
            r.EmployeeID
            for r in this_model.query.filter(
                or_(this_model.PackageCode.in_(pkg_vars), _sql_norm_pkg(this_model.PackageCode).in_(pkg_vars))
            ).all()
        ]
        other_raw = [
            r.EmployeeID
            for r in other_model.query.filter(
                or_(other_model.PackageCode.in_(pkg_vars), _sql_norm_pkg(other_model.PackageCode).in_(pkg_vars))
            ).all()
        ]
        preselected_norm = _resolve_hr_employeeids(this_raw)
        locked_norm = _resolve_hr_employeeids(other_raw) - preselected_norm

    pinned_checked, pinned_locked = set(preselected_norm), set(locked_norm)

    # search employees
    emp_search_q = emp_q
    if search:
        terms = _search_terms(search)
        likes = [f"%{t}%" for t in terms if t]
        conds = []
        for lk in likes:
            conds += [HRProfile.EmployeeID.like(lk), HRProfile.FullName.like(lk), HRProfile.StaffCode.like(lk)]
        if conds:
            emp_search_q = emp_search_q.filter(or_(*conds))

    employees_search = emp_search_q.order_by(HRProfile.FullName.asc()).all()

    pinned_emps = []
    if pinned_checked or pinned_locked:
        pinned_emps = emp_q.filter(_sql_norm(HRProfile.EmployeeID).in_(list(pinned_checked | pinned_locked))).all()

    employees = _merge_employees(pinned_emps, employees_search, pinned_checked, pinned_locked)

    if request.method == "POST":
        if _save_group(pkg, this_model, other_model, _members_norm(), ok_msg):
            return redirect(url_for("procurement.list_packages"))

    return render_template(
        template,
        packages=packages,
        employees=employees,
        search=search,
        selected_package=pkg,
        preselected_norm=pinned_checked,
        locked_norm=pinned_locked,
    )


@procurement_bp.route("/expert-group", methods=["GET", "POST"])
@login_required
@check_permission("procurement", "update")
def expert_group():
    return _group_page(
        "procurement_expert_group.html",
        TenderExpertMember,
        TenderAppraisalMember,
        "✅ Đã lưu Tổ chuyên gia.",
        filter_by_dept=False,
    )


@procurement_bp.route("/appraisal-group", methods=["GET", "POST"])
@login_required
@check_permission("procurement", "update")
def appraisal_group():
    return _group_page(
        "procurement_appraisal_group.html",
        TenderAppraisalMember,
        TenderExpertMember,
        "✅ Đã lưu Tổ thẩm định.",
        filter_by_dept=False,
    )
