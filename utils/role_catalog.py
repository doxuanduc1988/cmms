"""
Danh mục vai trò chuẩn và ánh xạ vai trò legacy (tên tiếng Việt) → mã chuẩn.
"""
from __future__ import annotations

from models.roles import Role

# Vai trò dùng trong UI gán user (không hiện bản legacy trùng nghĩa)
CANONICAL_ROLE_CODES = frozenset(
    {
        "admin",
        "nhansu",
        "hanhchinh",
        "truongphong",
        "muasam",
        "du_toan",
        "lanhdao",
        "canbo",
    }
)

CANONICAL_ROLE_LABELS = {
    "admin": "Quản trị hệ thống (admin)",
    "nhansu": "Nhân sự (nhansu)",
    "hanhchinh": "Hành chính (hanhchinh)",
    "truongphong": "Trưởng phòng (truongphong)",
    "muasam": "Mua sắm & đấu thầu (muasam)",
    "du_toan": "Dự toán (du_toan)",
    "lanhdao": "Lãnh đạo xem báo cáo (lanhdao)",
    "canbo": "Cán bộ (canbo)",
}

# Tên legacy (lower) → mã vai trò chuẩn
LEGACY_ROLE_TO_CANONICAL = {
    "đấu thầu": "muasam",
    "dau thau": "muasam",
    "mua sắm": "muasam",
    "dự toán": "du_toan",
    "du toan": "du_toan",
    "hồ sơ nhân sự": "nhansu",
    "ho so nhan su": "nhansu",
    "tổng hợp chấm công": "hanhchinh",
    "tong hop cham cong": "hanhchinh",
    "chấm công": "hanhchinh",
    "cham cong": "hanhchinh",
    "phê duyệt công": "truongphong",
    "phe duyet cong": "truongphong",
    "y tế": "nhansu",
    "y te": "nhansu",
    "chỉ xem": "lanhdao",
    "chi xem": "lanhdao",
    "quản trị": "admin",
    "quan tri": "admin",
    "administrator": "admin",
}


def _normalize_role_name(name: str) -> str:
    return (name or "").strip().lower()


def is_canonical_role(role: Role) -> bool:
    code = _normalize_role_name(role.RoleName)
    if code in CANONICAL_ROLE_CODES:
        return True
    return code == "admin"


def canonical_code_for_role(role: Role) -> str | None:
    code = _normalize_role_name(role.RoleName)
    if code in CANONICAL_ROLE_CODES:
        return code
    if code == "admin":
        return "admin"
    return LEGACY_ROLE_TO_CANONICAL.get(code)


_FALLBACK_NAMES = {
    "du_toan": ["du_toan", "dự toán", "du toan"],
    "muasam": ["muasam", "đấu thầu", "mua sắm"],
    "admin": ["admin", "quản trị"],
}


def get_canonical_role_by_code(code: str) -> Role | None:
    code = code.strip().lower()
    names = _FALLBACK_NAMES.get(code, [code])
    for n in names:
        r = Role.query.filter(Role.RoleName.ilike(n)).first()
        if r:
            return r
    return None


def get_assignable_roles() -> list[Role]:
    """Vai trò hiển thị khi gán cho user — chỉ bản chuẩn, sắp xếp theo nhãn."""
    roles = Role.query.all()
    canonical = []
    for r in roles:
        c = canonical_code_for_role(r)
        if c and _normalize_role_name(r.RoleName) == c:
            canonical.append((c, r))
        elif r.RoleName.strip().lower() == "admin":
            canonical.append(("admin", r))
    # Một mã một role (ưu tiên role đầu tiên khớp mã)
    by_code: dict[str, Role] = {}
    for code, r in canonical:
        by_code.setdefault(code, r)
    order = list(CANONICAL_ROLE_CODES)
    return [by_code[c] for c in order if c in by_code]


def resolve_role_ids_to_canonical(role_ids: list) -> list[Role]:
    """Chuyển danh sách RoleID (có thể legacy) → vai trò chuẩn, không trùng."""
    if not role_ids:
        return []
    roles = Role.query.filter(Role.RoleID.in_(role_ids)).all()
    codes: set[str] = set()
    result: list[Role] = []
    for r in roles:
        code = canonical_code_for_role(r) or _normalize_role_name(r.RoleName)
        if code in codes:
            continue
        target = get_canonical_role_by_code(code) if code in CANONICAL_ROLE_CODES or code == "admin" else r
        if not target:
            target = r
        c2 = canonical_code_for_role(target) or _normalize_role_name(target.RoleName)
        if c2 in codes:
            continue
        codes.add(c2)
        result.append(target)
    return result
