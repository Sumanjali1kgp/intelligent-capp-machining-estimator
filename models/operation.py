from extensions import db

class Operation(db.Model):
    """Model for storing different types of operations."""
    __tablename__ = 'Operations'  # Match the actual table name in the database
    __table_args__ = {'extend_existing': True}  # Allow table redefinition
    
    operation_id = db.Column(db.Integer, primary_key=True)
    operation_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Relationships with overlaps parameter to resolve SQLAlchemy warnings
    parameters = db.relationship(
        'MachiningParameter',
        backref='operation_ref',
        lazy=True,
        overlaps="operation,parameters"
    )
    
    def __repr__(self):
        return f'<Operation {self.operation_name}>'
