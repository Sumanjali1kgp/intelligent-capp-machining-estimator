from flask import Blueprint, request, jsonify
from models.job_models import PartOperation, OperationMaster, Part
from models.operation import Operation
from extensions import db
from datetime import datetime
from importlib import import_module
from models.machining_parameter import get_parameters_for_operation

operation_bp = Blueprint('operation', __name__)

@operation_bp.route('/api/operations', methods=['GET'])
def list_operations():
    """Get all available machining operations"""
    try:
        operations = Operation.query.order_by(Operation.operation_id).all()
        
        return jsonify([{
            'operation_id': op.operation_id,
            'operation_name': op.operation_name,
            'description': op.description if hasattr(op, 'description') else ''
        } for op in operations])
    except Exception as e:
        return jsonify({"message": f"Failed to fetch operations: {str(e)}"}), 500

@operation_bp.route('/api/parts/<int:part_id>/operations', methods=['POST'])
def create_operation(part_id):
    """Create a new operation for a part"""
    data = request.get_json()
    
    required_fields = ['name', 'machining_time', 'machining_cost']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    
    try:
        part = Part.query.get_or_404(part_id)
        
        operation = Operation(
            part_id=part_id,
            name=data['name'],
            type=data.get('type', 'general'),
            machining_time=float(data['machining_time']),
            machining_cost=float(data['machining_cost']),
            tooling_cost=float(data.get('tooling_cost', 0)),
            parameters=data.get('parameters', {})
        )
        
        db.session.add(operation)
        
        # Update part's updated_at timestamp
        part.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        operation_data = {
            'id': operation.id,
            'name': operation.name,
            'type': operation.type,
            'machining_time': operation.machining_time,
            'machining_cost': operation.machining_cost,
            'tooling_cost': operation.tooling_cost,
            'created_at': operation.created_at.isoformat() if operation.created_at else None
        }
        
        return jsonify(operation_data), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to create operation: {str(e)}"}), 500

@operation_bp.route('/api/operations/<int:operation_id>', methods=['GET'])
def get_operation(operation_id):
    """Get a single operation"""
    try:
        operation = Operation.query.get_or_404(operation_id)
        
        operation_data = {
            'id': operation.id,
            'part_id': operation.part_id,
            'name': operation.name,
            'type': operation.type,
            'machining_time': operation.machining_time,
            'machining_cost': operation.machining_cost,
            'tooling_cost': operation.tooling_cost,
            'created_at': operation.created_at.isoformat() if operation.created_at else None,
            'updated_at': operation.updated_at.isoformat() if operation.updated_at else None
        }
        
        return jsonify(operation_data)
    except Exception as e:
        return jsonify({"message": f"Failed to fetch operation: {str(e)}"}), 500

@operation_bp.route('/api/operations/<int:operation_id>', methods=['PUT'])
def update_operation(operation_id):
    """Update an operation"""
    data = request.get_json()
    
    try:
        operation = Operation.query.get_or_404(operation_id)
        part = Part.query.get_or_404(operation.part_id)
        
        # Update fields if they exist in the request
        if 'name' in data:
            operation.name = data['name']
        if 'type' in data:
            operation.type = data['type']
        if 'machining_time' in data:
            operation.machining_time = float(data['machining_time'])
        if 'machining_cost' in data:
            operation.machining_cost = float(data['machining_cost'])
        if 'tooling_cost' in data:
            operation.tooling_cost = float(data['tooling_cost'])
        if 'parameters' in data:
            operation.parameters = data['parameters']
        
        # Update timestamps
        operation.updated_at = datetime.utcnow()
        part.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        operation_data = {
            'id': operation.id,
            'part_id': operation.part_id,
            'name': operation.name,
            'type': operation.type,
            'machining_time': operation.machining_time,
            'machining_cost': operation.machining_cost,
            'tooling_cost': operation.tooling_cost,
            'updated_at': operation.updated_at.isoformat() if operation.updated_at else None
        }
        
        return jsonify(operation_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to update operation: {str(e)}"}), 500

@operation_bp.route('/api/operations/<int:operation_id>', methods=['DELETE'])
def delete_operation(operation_id):
    """Delete an operation"""
    try:
        operation = Operation.query.get_or_404(operation_id)
        part = Part.query.get_or_404(operation.part_id)
        
        # Store part_id for response before deletion
        part_id = operation.part_id
        
        # Update part's updated_at timestamp
        part.updated_at = datetime.utcnow()
        
        # Delete the operation
        db.session.delete(operation)
        db.session.commit()
        
        return jsonify({
            "message": "Operation deleted successfully",
            "part_id": part_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to delete operation: {str(e)}"}), 500
@operation_bp.route('/api/operations/calculate', methods=['POST'])
def calculate_operation():
    """
    Generic calculation route for all operations (turning, drilling, milling, etc.)
    Uses user-provided feed/spindle values if given, else DB defaults.
    """
    try:
        data = request.get_json()

        # --- Required fields ---
        operation_type = data.get('operation_type')  # e.g., "turning"
        material_id = data.get('material_id')
        operation_id = data.get('operation_id')
        material_rating = float(data.get('material_rating', 1.0))
        input_dims = data.get('dimensions', {})

        if not all([operation_type, material_id, operation_id]):
            return jsonify({'error': 'Missing required fields: operation_type, material_id, operation_id'}), 400

        # --- Dynamically import correct operation class ---
        try:
            module = import_module(f"models.{operation_type.lower()}")
            operation_class = getattr(module, f"{operation_type.capitalize()}Operation")
        except (ImportError, AttributeError):
            return jsonify({'error': f"Unsupported operation type: {operation_type}"}), 400

        # --- Fetch parameters from DB ---
        db_params = get_parameters_for_operation(material_id, operation_id)

        # --- Initialize operation ---
        operation_instance = operation_class(db_params, material_rating, input_dims)

        # --- User-provided overrides (optional) ---
        overrides = {
            'feed': data.get('feed'),
            'spindle_speed': data.get('spindle_speed')
        }


        # --- Perform calculation ---
        result = operation_instance.calculate(inputs=overrides)
        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify({'error': f"{str(e)}\n{traceback.format_exc()}"}), 500