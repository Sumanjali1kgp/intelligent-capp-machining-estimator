from flask import Blueprint, jsonify
from extensions import db
from models.material import Material
from models.machining_parameter import MachiningParameter

material_bp = Blueprint('material', __name__)

@material_bp.route('/api/materials', methods=['GET'])
def get_materials():
    """Get all materials with machinability and tooling information"""
    try:
        materials = Material.query.all()
        return jsonify([{
            'material_id': m.material_id,
            'material_name': m.material_name,
            'machinability_rating': float(m.machinability_rating) if m.machinability_rating is not None else 0.5,  # Default to 0.5 if not set
            'recommended_tool': m.recommended_tool or 'HSS',  # Default to HSS if not specified
            'notes': m.notes or ''
        } for m in materials])
    except Exception as e:
        return jsonify({
            "error": "Failed to fetch materials",
            "message": str(e),
            "type": type(e).__name__
        }), 500

# @material_bp.route('/api/operations', methods=['GET'])
# def get_operations():
#     """Get all operation types"""
#     try:
#         # Get all unique operation types from the database
#         from sqlalchemy import distinct, func
#         from models.operation import Operation  # Import the Operation model
        
#         # Query distinct operation types from the Operation model
#         operations = db.session.query(
#             Operation.operation_id,
#             Operation.operation_name
#         ).distinct().all()
        
#         return jsonify([{
#             'id': op.operation_id,
#             'name': op.operation_name,
#             'code': op.operation_name.lower().replace(' ', '_')
#         } for i, op in enumerate(operations)])
#     except Exception as e:
#         return jsonify({"message": f"Failed to fetch operations: {str(e)}"}), 500
