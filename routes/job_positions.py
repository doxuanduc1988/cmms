# routes/job_positions.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models.hr.job_position_model import JobPosition
from extensions import db
from utils.permission_utils import check_permission

job_position_bp = Blueprint("job_positions", __name__, url_prefix="/job_positions")


# Danh sách JobPositions
@job_position_bp.route("/", methods=["GET"])
@login_required
@check_permission("hr", "read")
def list_job_positions():
    positions = JobPosition.query.order_by(JobPosition.JobPositionName).all()
    return render_template("job_positions/list.html", positions=positions)


# Thêm mới JobPosition
@job_position_bp.route("/create", methods=["GET", "POST"])
@login_required
@check_permission("hr", "create")
def create_job_position():
    if request.method == "POST":
        code = request.form.get("job_position_code")
        name = request.form.get("job_position_name")
        description = request.form.get("description")

        new_position = JobPosition(JobPositionCode=code, JobPositionName=name, Description=description)

        db.session.add(new_position)
        db.session.commit()
        flash("Thêm chức danh mới thành công!", "success")
        return redirect(url_for("job_positions.list_job_positions"))

    return render_template("job_positions/create.html")


# Chỉnh sửa JobPosition
@job_position_bp.route("/edit/<int:position_id>", methods=["GET", "POST"])
@login_required
@check_permission("hr", "update")
def edit_job_position(position_id):
    position = JobPosition.query.get_or_404(position_id)

    if request.method == "POST":
        position.JobPositionCode = request.form.get("job_position_code")
        position.JobPositionName = request.form.get("job_position_name")
        position.Description = request.form.get("description")

        db.session.commit()
        flash("Cập nhật chức danh thành công!", "success")
        return redirect(url_for("job_positions.list_job_positions"))

    return render_template("job_positions/edit.html", position=position)


# Xóa JobPosition
@job_position_bp.route("/delete/<int:position_id>", methods=["POST"])
@login_required
@check_permission("hr", "delete")
def delete_job_position(position_id):
    position = JobPosition.query.get_or_404(position_id)
    db.session.delete(position)
    db.session.commit()
    flash("Xóa chức danh thành công!", "success")
    return redirect(url_for("job_positions.list_job_positions"))
