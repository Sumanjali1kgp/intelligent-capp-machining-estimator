from flask import Blueprint, request, jsonify, url_for
from models.job_models import Part, Job, PartOperation, OperationMaster
from extensions import db
from datetime import datetime

part_bp = Blueprint('part', __name__)

@part_bp.route('/api/jobs/<int:job_id>/parts', methods=['GET'])
def get_job_parts(job_id):
    """Get all parts for a job"""
    try:
        job = Job.query.get_or_404(job_id)
        parts_data = []
        
        for part in job.parts:
            part_data = {
                'id': part.id,
                'name': part.name,
                'material_cost': part.material_cost,
                'total_time': part.total_time or 0,
                'total_cost': part.total_cost or part.material_cost,
                'notes': getattr(part, 'notes', '')
            }
            parts_data.append(part_data)
            
        return jsonify(parts_data)
    except Exception as e:
        return jsonify({"message": f"Failed to fetch parts: {str(e)}"}), 500

@part_bp.route('/api/jobs/<int:job_id>/parts', methods=['POST'])
def create_part(job_id):
    """Create a new part for a job"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({"message": "Part name is required"}), 400
    
    try:
        job = Job.query.get_or_404(job_id)
        
        part = Part(
            job_id=job_id,
            name=data['name'],
            material_cost=float(data.get('material_cost', 0)),
            notes=data.get('notes', '')
        )
        
        db.session.add(part)
        db.session.commit()
        
        part_data = {
            'id': part.id,
            'name': part.name,
            'material_cost': part.material_cost,
            'total_time': 0,
            'total_cost': part.material_cost,
            'notes': part.notes
        }
        
        return jsonify(part_data), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to create part: {str(e)}"}), 500

@part_bp.route('/api/parts/<int:part_id>', methods=['GET'])
def get_part(part_id):
    """Get a specific part with its operations"""
    try:
        part = Part.query.get_or_404(part_id)
        
        part_data = {
            'id': part.id,
            'name': part.name,
            'material_cost': part.material_cost,
            'total_time': part.total_time or 0,
            'total_cost': part.total_cost or part.material_cost,
            'notes': getattr(part, 'notes', '')
        }
        
        return jsonify(part_data)
    except Exception as e:
        return jsonify({"message": f"Failed to fetch part: {str(e)}"}), 500

@part_bp.route('/api/parts/<int:part_id>', methods=['PUT'])
def update_part(part_id):
    """Update a part"""
    try:
        part = Part.query.get_or_404(part_id)
        data = request.get_json()
        
        if 'name' in data:
            part.name = data['name']
        if 'material_cost' in data:
            part.material_cost = float(data['material_cost'])
        if 'notes' in data:
            part.notes = data['notes']
        
        part.updated_at = datetime.utcnow()
        db.session.commit()
        
        part_data = {
            'id': part.id,
            'name': part.name,
            'material_cost': part.material_cost,
            'total_time': part.total_time or 0,
            'total_cost': part.total_cost or part.material_cost,
            'notes': getattr(part, 'notes', '')
        }
        
        return jsonify(part_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to update part: {str(e)}"}), 500

@part_bp.route('/api/parts/<int:part_id>', methods=['DELETE'])
def delete_part(part_id):
    """Delete a part and its operations"""
    try:
        part = Part.query.get_or_404(part_id)
        job_id = part.job_id
        
        # Delete all operations first
        Operation.query.filter_by(part_id=part_id).delete()
        
        # Then delete the part
        db.session.delete(part)
        db.session.commit()
        
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to delete part: {str(e)}"}), 500

@part_bp.route('/api/parts/<int:part_id>/operations', methods=['GET'])
def get_part_operations(part_id):
    """Get all operations for a part"""
    try:
        part = Part.query.get_or_404(part_id)
        operations = []
        
        for op in part.operations:
            operations.append({
                'id': op.id,
                'name': op.name,
                'machining_time': op.machining_time,
                'machining_cost': op.machining_cost,
                'tooling_cost': op.tooling_cost,
                'type': getattr(op, 'type', 'general')
            })
            
        return jsonify(operations)
    except Exception as e:
        return jsonify({"message": f"Failed to fetch operations: {str(e)}"}), 500

@part_bp.route('/api/parts/<int:part_id>/calculate', methods=['GET'])
def calculate_part(part_id):
    """Calculate total time and cost for a part"""
    try:
        part = Part.query.get_or_404(part_id)
        
        total_time = sum(op.machining_time for op in part.operations)
        total_cost = part.material_cost + sum(
            op.machining_cost + op.tooling_cost 
            for op in part.operations
        )
        
        # Update part totals
        part.total_time = total_time
        part.total_cost = total_cost
        db.session.commit()
        
        return jsonify({
            "part_id": part_id,
            "total_time": total_time,
            "total_cost": total_cost,
            "material_cost": part.material_cost,
            "details": [{
                'op_name': op.name,
                'time': op.machining_time,
                'cost': op.machining_cost + op.tooling_cost
            } for op in part.operations]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to calculate part: {str(e)}"}), 500
