# utils/salary_utils.py (helper dùng chung – khuyến nghị)
from decimal import Decimal
from models.hr_salary_history import HRSalaryHistory


def get_latest_coefficient(employee_id):
    latest = (
        HRSalaryHistory.query.filter_by(EmployeeID=employee_id)
        .order_by(HRSalaryHistory.EffectiveDate.desc(), HRSalaryHistory.SalaryID.desc())  # tie-break khi cùng ngày
        .first()
    )
    if not latest:
        return None, None
    try:
        coef = Decimal(str(latest.Coefficient)) if latest.Coefficient is not None else None
    except Exception:
        coef = None
    return coef, latest.EffectiveDate
