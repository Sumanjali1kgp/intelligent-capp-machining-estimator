from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from models.job_models import Job, Part, PartOperation, OperationMaster
from extensions import db
from datetime import datetime

job_bp = Blueprint('job', __name__, url_prefix='/jobs')

@job_bp.route('/', methods=['GET'])
def list_jobs():
    """List all saved jobs"""
    jobs = Job.query.order_by(Job.updated_at.desc()).all()
    return render_template('saved_jobs.html', jobs=jobs)

@job_bp.route('/create', methods=['GET', 'POST'])
def create_job():
    """Create a new job"""
    if request.method == 'POST':
        job_name = request.form.get('job_name')
        if not job_name:
            flash('Job name is required', 'error')
            return render_template('index.html')
            
        job = Job(name=job_name)
        db.session.add(job)
        db.session.commit()
        
        # Redirect to add parts to the job
        return redirect(url_for('job.add_part', job_id=job.id))
    
    return render_template('index.html')

@job_bp.route('/<int:job_id>/add_part', methods=['GET', 'POST'])
def add_part(job_id):
    """Add a new part to a job"""
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        part_name = request.form.get('part_name')
        material_cost = float(request.form.get('material_cost', 0))
        
        part = Part(name=part_name, material_cost=material_cost, job_id=job_id)
        db.session.add(part)
        db.session.commit()
        
        # Redirect to add operations to the part
        return redirect(url_for('job.add_operation', job_id=job_id, part_id=part.id))
    
    return render_template('parts.html', job=job)

@job_bp.route('/<int:job_id>/parts/<int:part_id>/add_operation', methods=['GET', 'POST'])
def add_operation(job_id, part_id):
    """Add a new operation to a part"""
    job = Job.query.get_or_404(job_id)
    part = Part.query.get_or_404(part_id)
    
    if request.method == 'POST':
        # Get operation data from form
        operation_type = request.form.get('operation_type')
        operation_name = request.form.get('operation_name')
        machining_time = float(request.form.get('machining_time', 0))
        machining_cost = float(request.form.get('machining_cost', 0))
        tooling_cost = float(request.form.get('tooling_cost', 0))
        
        # Create a dictionary of all parameters
        parameters = {
            k: v for k, v in request.form.items() 
            if k not in ['operation_type', 'operation_name', 'machining_time', 'machining_cost', 'tooling_cost']
        }
        
        operation = Operation(
            part_id=part_id,
            type=operation_type,
            name=operation_name,
            machining_time=machining_time,
            machining_cost=machining_cost,
            tooling_cost=tooling_cost,
            parameters=parameters
        )
        
        db.session.add(operation)
        db.session.commit()
        
        # Redirect back to add another operation or finish
        if 'add_another' in request.form:
            return redirect(url_for('job.add_operation', job_id=job_id, part_id=part_id))
        return redirect(url_for('job.view_job', job_id=job_id))
    
    return render_template('operation_form.html', job=job, part=part)

@job_bp.route('/<int:job_id>', methods=['GET'])
def view_job(job_id):
    """View job details"""
    job = Job.query.get_or_404(job_id)
    return render_template('job_details.html', job=job)

@job_bp.route('/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    """Edit job details"""
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        job.name = request.form.get('job_name', job.name)
        db.session.commit()
        return redirect(url_for('job.view_job', job_id=job_id))
    
    return render_template('edit_job.html', job=job)

@job_bp.route('/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job"""
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('job.list_jobs'))

# API endpoints for AJAX operations
@job_bp.route('/api/jobs', methods=['GET'])
def api_list_jobs():
    """API endpoint to get all jobs (for AJAX)"""
    jobs = Job.query.order_by(Job.updated_at.desc()).all()
    return jsonify([job.to_dict() for job in jobs])

@job_bp.route('/api/jobs/<int:job_id>', methods=['GET'])
def api_get_job(job_id):
    """API endpoint to get a specific job (for AJAX)"""
    job = Job.query.get_or_404(job_id)
    return jsonify(job.to_dict())
