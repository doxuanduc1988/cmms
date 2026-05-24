# routes/crew_route.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.attendance.crew_model import CrewDefinition
from utils.permission_utils import check_permission

crew_bp = Blueprint("crew", __name__, url_prefix="/crews")


@crew_bp.route("/")
@check_permission("crew", "read")
def crew_list():
    crews = CrewDefinition.query.order_by(CrewDefinition.CrewCode).all()
    return render_template("crews/crew_list.html", crews=crews)


@crew_bp.route("/create", methods=["GET", "POST"])
@check_permission("crew", "create")
def create_crew():
    if request.method == "POST":
        crew = CrewDefinition(
            CrewCode=request.form["CrewCode"],
            CrewName=request.form["CrewName"],
            Description=request.form.get("Description"),
        )
        db.session.add(crew)
        db.session.commit()
        flash("Đã thêm kíp thành công!", "success")
        return redirect(url_for("crew.crew_list"))
    return render_template("crews/crew_form.html", action="create")


@crew_bp.route("/<int:crew_id>/edit", methods=["GET", "POST"])
@check_permission("crew", "update")
def edit_crew(crew_id):
    crew = CrewDefinition.query.get_or_404(crew_id)
    if request.method == "POST":
        crew.CrewCode = request.form["CrewCode"]
        crew.CrewName = request.form["CrewName"]
        crew.Description = request.form.get("Description")
        db.session.commit()
        flash("Đã cập nhật kíp thành công!", "success")
        return redirect(url_for("crew.crew_list"))
    return render_template("crews/crew_form.html", crew=crew, action="edit")


@crew_bp.route("/<int:crew_id>/delete", methods=["POST"])
@check_permission("crew", "delete")
def delete_crew(crew_id):
    crew = CrewDefinition.query.get_or_404(crew_id)
    db.session.delete(crew)
    db.session.commit()
    flash("Đã xoá kíp.", "info")
    return redirect(url_for("crew.crew_list"))
