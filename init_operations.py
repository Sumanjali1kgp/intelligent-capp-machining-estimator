from app import create_app
from models.job_models import Operation
from extensions import db

def init_operations():
    app = create_app()
    with app.app_context():
        # Define default operations
        default_operations = [
            {'type': 'turning', 'name': 'Facing'},
            {'type': 'turning', 'name': 'Turning'},
            {'type': 'turning', 'name': 'Drilling'},
            {'type': 'milling', 'name': 'Face Milling'},
            {'type': 'milling', 'name': 'End Milling'},
            {'type': 'milling', 'name': 'Slot Milling'},
        ]
        
        # Add operations to database if they don't exist
        for op_data in default_operations:
            if not Operation.query.filter_by(name=op_data['name']).first():
                operation = Operation(**op_data)
                db.session.add(operation)
        
        db.session.commit()
        print("Operations initialized successfully!")

if __name__ == '__main__':
    init_operations()
