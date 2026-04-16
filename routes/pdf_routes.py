from datetime import datetime
import os

from flask import Blueprint, jsonify, make_response, render_template
import pdfkit
from sqlalchemy.orm import joinedload

from extensions import db
from models.job_models import Job, Part, PartOperation


pdf_bp = Blueprint("pdf_bp", __name__)

WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
pdf_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH) if os.path.exists(WKHTMLTOPDF_PATH) else None


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _serialize_report_job(job):
    job_data = job.to_dict(include_parts=True)

    material_details = job.material.to_dict() if getattr(job, 'material', None) else None
    if material_details:
        job_data['material_name'] = material_details.get('material_name')
        job_data['material_rating'] = material_details.get('machinability_rating')

    job_data.update({
        'total_time': _safe_float(job.total_time),
        'total_machining_time': _safe_float(job.total_machining_time),
        'total_setup_time': _safe_float(job.total_setup_time),
        'total_tool_time': _safe_float(job.total_tool_time),
        'total_idle_time': _safe_float(job.total_idle_time),
        'total_misc_time': _safe_float(job.total_misc_time),
        'total_cost': _safe_float(job.total_cost),
        'material_cost': _safe_float(job.material_cost),
        'machining_cost': _safe_float(job.machining_cost),
        'tooling_cost': _safe_float(job.tooling_cost),
        'setup_idle_cost': _safe_float(job.setup_idle_cost),
        'misc_cost': _safe_float(job.misc_cost),
        'overhead_cost': _safe_float(job.overhead_cost),
    })

    serialized_parts = []
    for part in job.parts:
        part_data = part.to_dict(include_operations=True)
        part_material = getattr(part, 'material', None)
        part_data['material_name'] = (
            part_material.material_name
            if part_material else job_data.get('material_name')
        )
        part_data['material_rating'] = (
            part_material.machinability_rating
            if part_material else job_data.get('material_rating')
        )
        part_data['initial_length'] = part.initial_length
        part_data['initial_diameter'] = part.initial_diameter
        part_data['notes'] = part.description

        serialized_operations = []
        for operation in part.operations:
            operation_data = operation.to_dict()
            operation_data['operation_name'] = (
                operation_data.get('parameters', {}).get('operation_name')
                or (operation.operation.operation_name if operation.operation else None)
                or operation_data.get('operation_name')
            )
            serialized_operations.append(operation_data)

        part_data['operations'] = serialized_operations
        serialized_parts.append(part_data)

    job_data['parts'] = serialized_parts
    return job_data


def _get_report_job(job_id):
    return (
        Job.query.options(
            joinedload(Job.material),
            joinedload(Job.parts).joinedload(Part.material),
            joinedload(Job.parts).joinedload(Part.operations).joinedload(PartOperation.operation),
        )
        .get_or_404(job_id)
    )


def render_pdf(template, data, filename, report_type='shop'):
    if pdf_config is None:
        return jsonify({
            'error': 'wkhtmltopdf is not installed or not found at the configured path.'
        }), 500

    html = render_template(
        template,
        data=data,
        generated_on=datetime.now(),
        report_type=report_type,
    )
    pdf = pdfkit.from_string(
        html,
        False,
        configuration=pdf_config,
        options={"enable-local-file-access": ""},
    )
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@pdf_bp.route("/pdf/shop_floor/<int:job_id>")
def generate_shop_floor_pdf(job_id):
    job = _get_report_job(job_id)
    job_data = _serialize_report_job(job)
    return render_pdf(
        "pdf/shop_floor_report.html",
        job_data,
        f"ShopFloor_Report_{job_id}.pdf",
        report_type='shop',
    )


@pdf_bp.route("/pdf/customer/<int:job_id>")
def generate_customer_pdf(job_id):
    job = _get_report_job(job_id)
    job_data = _serialize_report_job(job)
    return render_pdf(
        "pdf/customer_report.html",
        job_data,
        f"Customer_Report_{job_id}.pdf",
        report_type='customer',
    )


@pdf_bp.route("/api/job_report/<int:job_id>")
def get_job_report(job_id):
    job = _get_report_job(job_id)
    return jsonify(_serialize_report_job(job))
