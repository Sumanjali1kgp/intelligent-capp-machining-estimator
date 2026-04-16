import logging
import os
from datetime import datetime
from importlib import import_module

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from extensions import db, migrate
from routes.pdf_routes import pdf_bp


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_CALCULATORS = {
    'turning': {
        'module_path': 'models.turning',
        'class_name': 'TurningOperation',
    },
    'taper turning': {
        'module_path': 'models.turning',
        'class_name': 'TurningOperation',
    },
    'contouring': {
        'module_path': 'models.turning',
        'class_name': 'TurningOperation',
    },
    'facing': {
        'module_path': 'models.facing',
        'class_name': 'FacingOperation',
    },
    'chamfering': {
        'module_path': 'models.facing',
        'class_name': 'FacingOperation',
    },
    'drilling': {
        'module_path': 'models.drilling',
        'class_name': 'DrillingOperation',
    },
    'boring': {
        'module_path': 'models.boring',
        'class_name': 'BoringOperation',
    },
    'milling': {
        'module_path': 'models.milling',
        'class_name': 'MillingOperation',
    },
    'reaming': {
        'module_path': 'models.reaming',
        'class_name': 'ReamingOperation',
    },
    'grooving': {
        'module_path': 'models.grooving',
        'class_name': 'GroovingOperation',
    },
    'threading': {
        'module_path': 'models.threading',
        'class_name': 'ThreadingOperation',
    },
    'knurling': {
        'module_path': 'models.knurling',
        'class_name': 'KnurlingOperation',
    },
    'parting': {
        'module_path': 'models.parting',
        'class_name': 'PartingOperation',
    },
}


def _normalize_operation_name(operation_name):
    return (operation_name or '').strip().lower()


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///machining.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    migrate.init_app(app, db, directory='migrations')

    from models.feature import Feature
    from models.feature_operation import FeatureOperation
    from models.job_models import Job, OperationMaster, Part, PartOperation
    from models.machining_parameter import MachiningParameter
    from models.material import Material

    with app.app_context():
        db.create_all()
        try:
            from setup_database import initialize_database

            initialize_database(force_reset=False)
        except Exception as exc:
            logger.warning("Reference data seed skipped: %s", exc)

    def commit_or_rollback():
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def serialize_supported_operations(operations):
        return [
            operation.to_dict()
            for operation in operations
            if _normalize_operation_name(operation.operation_name) in SUPPORTED_CALCULATORS
        ]

    @app.route('/api/materials', methods=['GET'])
    def get_materials():
        try:
            materials = Material.query.order_by(Material.material_name.asc()).all()
            return jsonify([
                {
                    'material_id': material.material_id,
                    'material_name': material.material_name,
                    'machinability_rating': material.machinability_rating,
                    'recommended_tool': material.recommended_tool,
                    'notes': material.notes,
                }
                for material in materials
            ])
        except Exception as exc:
            logger.error("Error fetching materials: %s", exc)
            return jsonify({'error': 'Failed to fetch materials', 'message': str(exc)}), 500

    @app.route('/api/features', methods=['GET'])
    def get_features():
        try:
            features = db.session.execute(
                text("SELECT feature_id, feature_name, description FROM Features ORDER BY feature_name")
            ).fetchall()
            return jsonify([
                {
                    'feature_id': feature_id,
                    'feature_name': feature_name,
                    'description': description or '',
                }
                for feature_id, feature_name, description in features
            ])
        except Exception as exc:
            logger.error("Error fetching features: %s", exc)
            return jsonify({'error': 'Failed to fetch features', 'message': str(exc)}), 500

    @app.route('/api/operations', methods=['GET'])
    def get_operations():
        try:
            operations = OperationMaster.query.order_by(OperationMaster.operation_name.asc()).all()
            return jsonify(serialize_supported_operations(operations))
        except Exception as exc:
            logger.error("Error fetching operations: %s", exc)
            return jsonify({'error': 'Failed to fetch operations', 'message': str(exc)}), 500

    @app.route('/api/feature_operations/<int:feature_id>', methods=['GET'])
    def get_operations_for_feature(feature_id):
        try:
            query = text(
                """
                SELECT o.operation_id, o.operation_name, o.description
                FROM FeatureOperations fo
                JOIN Operations o ON fo.operation_id = o.operation_id
                WHERE fo.feature_id = :feature_id
                ORDER BY o.operation_name
                """
            )
            rows = db.session.execute(query, {'feature_id': feature_id}).fetchall()
            operations = [
                {
                    'operation_id': operation_id,
                    'operation_name': operation_name,
                    'description': description or '',
                }
                for operation_id, operation_name, description in rows
                if _normalize_operation_name(operation_name) in SUPPORTED_CALCULATORS
            ]
            return jsonify(operations)
        except Exception as exc:
            logger.error("Error fetching operations for feature %s: %s", feature_id, exc)
            return jsonify({'error': 'Failed to fetch feature operations', 'message': str(exc)}), 500

    @app.route('/api/jobs', methods=['GET'])
    def get_jobs():
        try:
            jobs = (
                Job.query.options(joinedload(Job.parts))
                .order_by(Job.updated_at.desc())
                .all()
            )
            return jsonify([job.to_dict(include_parts=True) for job in jobs])
        except Exception as exc:
            logger.error("Error fetching jobs: %s", exc)
            return jsonify({'error': 'Failed to fetch jobs', 'message': str(exc)}), 500

    @app.route('/api/jobs/<int:job_id>', methods=['GET'])
    def get_job(job_id):
        try:
            job = (
                Job.query.options(
                    joinedload(Job.material),
                    joinedload(Job.feature),
                    joinedload(Job.parts).joinedload(Part.operations).joinedload(PartOperation.operation),
                )
                .filter_by(id=job_id)
                .first_or_404()
            )
            return jsonify(job.to_dict(include_parts=True))
        except Exception as exc:
            logger.error("Error fetching job %s: %s", job_id, exc)
            return jsonify({'error': 'Failed to fetch job', 'message': str(exc)}), 500

    @app.route('/api/jobs', methods=['POST'])
    def create_job():
        try:
            data = request.get_json() or {}
            if not data.get('name'):
                return jsonify({'error': 'Job name is required'}), 400

            job = Job(
                name=data['name'],
                client_name=data.get('client_name'),
                description=data.get('description'),
                due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            )
            db.session.add(job)
            commit_or_rollback()
            return jsonify(job.to_dict(include_parts=False)), 201
        except Exception as exc:
            logger.error("Error creating job: %s", exc, exc_info=True)
            return jsonify({'error': 'Failed to create job', 'message': str(exc)}), 500

    @app.route('/api/jobs/<int:job_id>', methods=['PUT'])
    def update_job(job_id):
        try:
            job = Job.query.get_or_404(job_id)
            data = request.get_json(force=True) or {}

            job.name = data.get('name', job.name)
            job.client_name = data.get('client_name', job.client_name)
            job.description = data.get('description', job.description)
            job.status = data.get('status', job.status)
            job.material_id = data.get('material_id', job.material_id)
            job.feature_id = data.get('feature_id', job.feature_id)
            job.operation_id = data.get('operation_id', job.operation_id)
            job.operation_name = data.get('operation_name', job.operation_name)

            if 'dimensions' in data:
                job.dimensions_json = data.get('dimensions') or {}

            for field in (
                'total_time',
                'total_machining_time',
                'total_setup_time',
                'total_tool_time',
                'total_idle_time',
                'total_misc_time',
                'total_cost',
                'material_cost',
                'machining_cost',
                'tooling_cost',
                'setup_idle_cost',
                'misc_cost',
                'overhead_cost',
            ):
                if field in data:
                    setattr(job, field, _safe_float(data.get(field), 0.0))

            if 'parts' in data and isinstance(data['parts'], list):
                for existing_part in list(job.parts):
                    db.session.delete(existing_part)
                db.session.flush()

                for index, part_data in enumerate(data['parts'], start=1):
                    part = Part(
                        job_id=job.id,
                        name=part_data.get('name') or f'Part-{index}',
                        description=part_data.get('description', ''),
                        quantity=part_data.get('quantity', 1),
                        material_id=part_data.get('material_id'),
                        material_volume=part_data.get('material_volume'),
                        initial_length=part_data.get('initial_length'),
                        initial_width=part_data.get('initial_width'),
                        initial_height=part_data.get('initial_height'),
                        initial_diameter=part_data.get('initial_diameter'),
                        final_length=part_data.get('final_length'),
                        final_width=part_data.get('final_width'),
                        final_height=part_data.get('final_height'),
                        final_diameter=part_data.get('final_diameter'),
                    )
                    db.session.add(part)
                    db.session.flush()

                    for sequence, operation_data in enumerate(part_data.get('operations', []), start=1):
                        db.session.add(
                            PartOperation(
                                part_id=part.id,
                                operation_id=operation_data.get('operation_id'),
                                sequence=operation_data.get('sequence', sequence),
                                machining_time=_safe_float(operation_data.get('machining_time')),
                                machining_cost=_safe_float(operation_data.get('machining_cost')),
                                tooling_cost=_safe_float(operation_data.get('tooling_cost')),
                                parameters=operation_data.get('parameters') or {},
                            )
                        )

            job.updated_at = datetime.utcnow()
            commit_or_rollback()
            return jsonify(job.to_dict(include_parts=True))
        except Exception as exc:
            logger.error("Error updating job %s: %s", job_id, exc, exc_info=True)
            return jsonify({'error': 'Failed to update job', 'message': str(exc)}), 500

    @app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
    def delete_job(job_id):
        try:
            job = Job.query.get_or_404(job_id)
            db.session.delete(job)
            commit_or_rollback()
            return jsonify({'message': f'Job {job_id} deleted successfully'})
        except Exception as exc:
            logger.error("Error deleting job %s: %s", job_id, exc)
            return jsonify({'error': 'Failed to delete job', 'message': str(exc)}), 500

    @app.route('/api/jobs/<int:job_id>/parts', methods=['GET'])
    def get_job_parts(job_id):
        try:
            job = Job.query.get_or_404(job_id)
            return jsonify([part.to_dict(include_operations=True) for part in job.parts])
        except Exception as exc:
            logger.error("Error fetching parts for job %s: %s", job_id, exc)
            return jsonify({'error': 'Failed to fetch parts', 'message': str(exc)}), 500

    @app.route('/api/jobs/<int:job_id>/parts', methods=['POST'])
    def create_part(job_id):
        try:
            data = request.get_json() or {}
            if not data.get('name'):
                return jsonify({'error': 'Part name required'}), 400

            part = Part(
                job_id=job_id,
                name=data['name'],
                description=data.get('description', ''),
                material_id=data.get('material_id'),
                quantity=data.get('quantity', 1),
            )
            db.session.add(part)
            commit_or_rollback()
            return jsonify(part.to_dict(include_operations=False)), 201
        except Exception as exc:
            logger.error("Error creating part for job %s: %s", job_id, exc)
            return jsonify({'error': 'Failed to create part', 'message': str(exc)}), 500

    @app.route('/api/parts/<int:part_id>', methods=['PUT'])
    def update_part(part_id):
        try:
            part = Part.query.get_or_404(part_id)
            data = request.get_json() or {}

            part.name = data.get('name', part.name)
            part.description = data.get('description', part.description)
            part.material_id = data.get('material_id', part.material_id)
            part.quantity = data.get('quantity', part.quantity)
            commit_or_rollback()
            return jsonify(part.to_dict(include_operations=True))
        except Exception as exc:
            logger.error("Error updating part %s: %s", part_id, exc)
            return jsonify({'error': 'Failed to update part', 'message': str(exc)}), 500

    @app.route('/api/parts/<int:part_id>', methods=['DELETE'])
    def delete_part(part_id):
        try:
            part = Part.query.get_or_404(part_id)
            db.session.delete(part)
            commit_or_rollback()
            return jsonify({'message': f'Part {part_id} deleted successfully'})
        except Exception as exc:
            logger.error("Error deleting part %s: %s", part_id, exc)
            return jsonify({'error': 'Failed to delete part', 'message': str(exc)}), 500

    @app.route('/api/parts/<int:part_id>/operations', methods=['GET'])
    def get_part_operations(part_id):
        try:
            part = Part.query.get_or_404(part_id)
            return jsonify([operation.to_dict() for operation in part.operations])
        except Exception as exc:
            logger.error("Error fetching operations for part %s: %s", part_id, exc)
            return jsonify({'error': 'Failed to fetch operations', 'message': str(exc)}), 500

    @app.route('/api/parts/<int:part_id>/operations', methods=['POST'])
    def create_part_operation(part_id):
        try:
            data = request.get_json() or {}
            if 'operation_id' not in data:
                return jsonify({'error': 'Missing required operation_id'}), 400

            operation = PartOperation(
                part_id=part_id,
                operation_id=data['operation_id'],
                machining_time=_safe_float(data.get('machining_time')),
                machining_cost=_safe_float(data.get('machining_cost')),
                tooling_cost=_safe_float(data.get('tooling_cost')),
                parameters=data.get('parameters') or {},
            )
            db.session.add(operation)
            commit_or_rollback()
            return jsonify(operation.to_dict()), 201
        except Exception as exc:
            logger.error("Error creating operation for part %s: %s", part_id, exc)
            return jsonify({'error': 'Failed to create operation', 'message': str(exc)}), 500

    @app.route('/api/operations/<int:op_id>', methods=['PUT'])
    def update_operation(op_id):
        try:
            operation = PartOperation.query.get_or_404(op_id)
            data = request.get_json() or {}
            operation.machining_time = _safe_float(data.get('machining_time'), operation.machining_time)
            operation.machining_cost = _safe_float(data.get('machining_cost'), operation.machining_cost)
            operation.tooling_cost = _safe_float(data.get('tooling_cost'), operation.tooling_cost)
            operation.parameters = data.get('parameters', operation.parameters)
            commit_or_rollback()
            return jsonify(operation.to_dict())
        except Exception as exc:
            logger.error("Error updating operation %s: %s", op_id, exc)
            return jsonify({'error': 'Failed to update operation', 'message': str(exc)}), 500

    @app.route('/api/operations/<int:op_id>', methods=['DELETE'])
    def delete_operation(op_id):
        try:
            operation = PartOperation.query.get_or_404(op_id)
            db.session.delete(operation)
            commit_or_rollback()
            return jsonify({'message': f'Operation {op_id} deleted successfully'})
        except Exception as exc:
            logger.error("Error deleting operation %s: %s", op_id, exc)
            return jsonify({'error': 'Failed to delete operation', 'message': str(exc)}), 500

    @app.route('/api/calculate', methods=['POST'])
    def calculate_operation():
        try:
            data = request.get_json(force=True) or {}
            required_fields = ('material_id', 'operation_id', 'operation_name', 'dimensions')
            if any(field not in data for field in required_fields):
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

            operation_type = _normalize_operation_name(data['operation_name'])
            if operation_type not in SUPPORTED_CALCULATORS:
                return jsonify({'status': 'error', 'message': f'Unsupported operation: {data["operation_name"]}'}), 400

            material = db.session.get(Material, data['material_id'])
            if material is None:
                return jsonify({'status': 'error', 'message': 'Material not found'}), 404

            parameter_rows = (
                MachiningParameter.query
                .filter_by(material_id=data['material_id'], operation_id=data['operation_id'])
                .all()
            )
            if not parameter_rows:
                return jsonify({'status': 'error', 'message': 'No parameters found'}), 404

            calculator_config = SUPPORTED_CALCULATORS[operation_type]
            module = import_module(calculator_config['module_path'])
            calculator_class = getattr(module, calculator_config['class_name'])
            calculator = calculator_class(
                parameter_rows,
                material.machinability_rating or 1.0,
                data['dimensions'],
            )
            overrides = {
                'feed': data.get('feed'),
                'spindle_speed': data.get('spindle_speed'),
            }
            result = calculator.calculate(overrides)

            if isinstance(result, dict) and result.get('error'):
                return jsonify({'status': 'error', 'message': result['error']}), 400

            result.update(
                {
                    'material': material.material_name,
                    'operation': operation_type,
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )
            return jsonify(
                {
                    'status': 'success',
                    'time': result.get('total_time_minutes', 0),
                    'data': result,
                }
            )
        except Exception as exc:
            logger.error("Calculation error: %s", exc, exc_info=True)
            return jsonify({'status': 'error', 'message': str(exc)}), 500

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/lathe')
    def lathe():
        return render_template('lathe.html')

    @app.route('/milling')
    def milling():
        return render_template('milling.html')

    app.register_blueprint(pdf_bp)
    return app


if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, host='0.0.0.0', port=5000)
