from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from datetime import datetime
from models.hr.hr_profiles import HRProfile
from models.hr_contract_model import HRContract
from utils.permission_utils import check_permission
from models.hr_salary_table import HRSalaryTable
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads/contracts"
ALLOWED_EXTENSIONS = {"pdf", "docx", "jpg", "png"}

contract_bp = Blueprint("contract", __name__, url_prefix="/hr")


@contract_bp.route("/<employee_id>/contracts")
@check_permission("hr", "read")
def list_contracts(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    records = HRContract.query.filter_by(EmployeeID=employee_id).order_by(HRContract.StartDate.desc()).all()
    return render_template("hr/contract_list.html", employee=employee, records=records)


@contract_bp.route("/<employee_id>/contracts/create", methods=["GET", "POST"])
@check_permission("hr", "create")
def create_contract(employee_id):
    employee = HRProfile.query.get_or_404(employee_id)
    salary_levels = HRSalaryTable.query.order_by(HRSalaryTable.SalaryCode).all()

    if request.method == "POST":
        uploaded_file = request.files.get("FileAttachment")
        filename = None
        if uploaded_file and uploaded_file.filename != "":
            filename = secure_filename(uploaded_file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            uploaded_file.save(os.path.join(UPLOAD_FOLDER, filename))

        record = HRContract(
            EmployeeID=employee_id,
            ContractNumber=request.form["ContractNumber"],
            ContractType=request.form["ContractType"],
            StartDate=request.form["StartDate"],
            EndDate=request.form.get("EndDate"),
            SalaryCode=request.form["SalaryCode"],
            Status=request.form["Status"],
            FileAttachment=request.form.get("FileAttachment"),
            Description=request.form.get("Description"),
        )
        db.session.add(record)
        db.session.commit()
        # flash("Đã thêm hợp đồng lao động", "success")
        flash("\u0110\u00e3 th\u00eam h\u1ee3p \u0111\u1ed3ng lao \u0111\u1ed9ng", "success")
        return redirect(url_for("contract.list_contracts", employee_id=employee_id))

    return render_template("hr/contract_form.html", employee=employee, action="create", salary_levels=salary_levels)


@contract_bp.route("/<employee_id>/contracts/<int:contract_id>/edit", methods=["GET", "POST"])
@check_permission("hr", "update")
def edit_contract(employee_id, contract_id):
    employee = HRProfile.query.get_or_404(employee_id)
    record = HRContract.query.get_or_404(contract_id)
    salary_levels = HRSalaryTable.query.order_by(HRSalaryTable.SalaryCode).all()

    if request.method == "POST":
        record.ContractNumber = request.form.get("ContractNumber")
        record.ContractType = request.form.get("ContractType")
        record.StartDate = request.form.get("StartDate")
        record.EndDate = request.form.get("EndDate")
        record.SalaryCode = request.form["SalaryCode"]
        record.Status = request.form["Status"]
        # record.FileAttachment=request.form.get("FileAttachment")
        record.Description = request.form.get("Description")

        uploaded_file = request.files.get("FileAttachment")
        if uploaded_file and uploaded_file.filename != "":
            filename = secure_filename(uploaded_file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            uploaded_file.save(os.path.join(UPLOAD_FOLDER, filename))
            record.FileAttachment = filename

        db.session.commit()
        # flash("Đã cập nhật hợp đồng", "success")
        flash("\u0110\u00e3 c\u1eadp nh\u1eadt h\u1ee3p \u0111\u1ed3ng", "success")

        return redirect(url_for("contract.list_contracts", employee_id=employee_id))

    return render_template(
        "hr/contract_form.html", employee=employee, record=record, action="edit", salary_levels=salary_levels
    )


@contract_bp.route("/<employee_id>/contracts/<int:contract_id>/delete", methods=["POST"])
@check_permission("hr", "delete")
def delete_contract(employee_id, contract_id):
    record = HRContract.query.get_or_404(contract_id)
    db.session.delete(record)
    db.session.commit()
    flash("\u0110\u00e3 xoá hợp đồng.", "info")
    return redirect(url_for("contract.list_contracts", employee_id=employee_id))
