from datetime import datetime
from extensions import db
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import validates
import math

# -------------------------------------------------------------------
# JOB MODEL
# -------------------------------------------------------------------
class Job(db.Model):
    """Represents a machining job/project that contains multiple parts."""
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, in_progress, completed, delivered
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Time tracking fields
    total_time = db.Column(db.Float, default=0.0)  # Total time in minutes
    total_machining_time = db.Column(db.Float, default=0.0)
    total_setup_time = db.Column(db.Float, default=0.0)
    total_tool_time = db.Column(db.Float, default=0.0)
    total_idle_time = db.Column(db.Float, default=0.0)
    total_misc_time = db.Column(db.Float, default=0.0)
    
    # Cost tracking fields
    total_cost = db.Column(db.Float, default=0.0)  # Total estimated cost in currency
    material_cost = db.Column(db.Float, default=0.0)
    setup_idle_cost = db.Column(db.Float, default=0.0)
    machining_cost = db.Column(db.Float, default=0.0)
    tooling_cost = db.Column(db.Float, default=0.0)
    misc_cost = db.Column(db.Float, default=0.0)
    overhead_cost = db.Column(db.Float, default=0.0)
    
    material_id = db.Column(db.Integer, db.ForeignKey('Materials.material_id'), nullable=True)
    
    # New fields for direct job-level operations
    feature_id = db.Column(db.Integer, db.ForeignKey('features.feature_id'), nullable=True)
    operation_id = db.Column(db.Integer, db.ForeignKey('Operations.operation_id'), nullable=True)
    operation_name = db.Column(db.String(100), nullable=True)
    dimensions_json = db.Column(db.JSON, nullable=True)  # Store the dimensions as JSON

    # Relationships
    parts = db.relationship('Part', backref='job', lazy=True, cascade='all, delete-orphan')
    material = db.relationship('Material', backref='jobs')
    feature = db.relationship('Feature', backref='jobs')

    # ----------------------------------------------------------------
    # Validation
    # ----------------------------------------------------------------
    @validates('name')
    def validate_name(self, key, name):
        if not name or not name.strip():
            raise ValueError("Job name cannot be empty")
        return name.strip()

    # ----------------------------------------------------------------
    # Methods to update calculated fields
    # ----------------------------------------------------------------
    def update_totals(self):
        """Update all calculated fields based on parts and operations."""
        self.total_machining_time = sum(part.total_machining_time for part in self.parts)
        self.total_setup_time = sum(part.total_setup_time for part in self.parts)
        self.total_tool_time = sum(op.tooling_cost for part in self.parts for op in part.operations)
        
        # Update costs
        self.material_cost = sum(part.material_cost for part in self.parts)
        self.machining_cost = sum(part.total_machining_cost for part in self.parts)
        self.tooling_cost = sum(op.tooling_cost for part in self.parts for op in part.operations)
        self.setup_idle_cost = sum(part.total_setup_cost for part in self.parts)
        
        # Calculate total time (sum of all time components)
        self.total_time = sum([
            self.total_machining_time,
            self.total_setup_time,
            self.total_tool_time,
            self.total_idle_time,
            self.total_misc_time
        ])
        
        # Calculate total cost (sum of all cost components)
        self.total_cost = sum([
            self.material_cost,
            self.machining_cost,
            self.tooling_cost,
            self.setup_idle_cost,
            self.misc_cost,
            self.overhead_cost
        ])
        
        return self

    # ----------------------------------------------------------------
    # Computed Properties
    # ----------------------------------------------------------------
    @property
    def part_count(self):
        return len(self.parts)

    @property
    def operation_count(self):
        return sum(len(part.operations) for part in self.parts)

    def calculate_estimated_completion(self, hours_per_day=8):
        """Estimate completion date based on machining + setup time."""
        from datetime import timedelta
        remaining_hours = (self.total_machining_time + self.total_setup_time) / 60
        working_days = math.ceil(remaining_hours / hours_per_day)
        current_date = datetime.utcnow()
        added_days = 0
        while added_days < working_days:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # Monday-Friday
                added_days += 1
        return current_date

    def to_dict(self, include_parts=True):
        data = {
            'id': self.id,
            'name': self.name,
            'client_name': self.client_name,
            'description': self.description,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            
            # Time tracking
            'total_time': self.total_time,
            'total_machining_time': self.total_machining_time,
            'total_setup_time': self.total_setup_time,
            'total_tool_time': self.total_tool_time,
            'total_idle_time': self.total_idle_time,
            'total_misc_time': self.total_misc_time,
            
            # Cost tracking
            'total_cost': self.total_cost,
            'material_cost': self.material_cost,
            'setup_idle_cost': self.setup_idle_cost,
            'machining_cost': self.machining_cost,
            'tooling_cost': self.tooling_cost,
            'misc_cost': self.misc_cost,
            'overhead_cost': self.overhead_cost,
            
            # References
            'material_id': self.material_id,
            'feature_id': self.feature_id,
            'operation_id': self.operation_id,
            'operation_name': self.operation_name,
            'dimensions': self.dimensions_json or {},
            
            # Counts
            'part_count': len(self.parts) if hasattr(self, 'parts') else 0,
            'operation_count': self.operation_count if hasattr(self, 'operation_count') else 0,
            'estimated_completion': (
                self.calculate_estimated_completion().isoformat()
                if hasattr(self, 'calculate_estimated_completion') and self.status != 'completed' 
                else None
            )
        }
        
        if include_parts and hasattr(self, 'parts'):
            data['parts'] = [p.to_dict() for p in self.parts]
            
        return data
        return data

# -------------------------------------------------------------------
# PART MODEL
# -------------------------------------------------------------------
class Part(db.Model):
    """Represents a part to be machined as part of a job."""
    __tablename__ = 'parts'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)

    # Material Info
    material_id = db.Column(db.Integer, db.ForeignKey('Materials.material_id'))
    material_volume = db.Column(db.Float)  # in cm³

    # Dimensions (mm)
    initial_length = db.Column(db.Float)
    initial_width = db.Column(db.Float)
    initial_height = db.Column(db.Float)
    initial_diameter = db.Column(db.Float)
    final_length = db.Column(db.Float)
    final_width = db.Column(db.Float)
    final_height = db.Column(db.Float)
    final_diameter = db.Column(db.Float)

    # Costs
    material_cost = db.Column(db.Float, default=0.0)
    setup_cost = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    operations = db.relationship(
        'PartOperation',
        back_populates='part',
        order_by='PartOperation.sequence',
        cascade='all, delete-orphan'
    )

    # ----------------------------------------------------------------
    # Validation
    # ----------------------------------------------------------------
    @validates('name')
    def validate_name(self, key, name):
        if not name or not name.strip():
            raise ValueError("Part name cannot be empty")
        return name.strip()

    @validates('quantity', 'material_volume')
    def validate_positive_values(self, key, value):
        if value is not None and value <= 0:
            raise ValueError(f"{key} must be positive")
        return value

    # ----------------------------------------------------------------
    # Computed Properties
    # ----------------------------------------------------------------
    @property
    def total_material_volume(self):
        if self.material_volume is not None:
            return self.material_volume * self.quantity
        return None

    @property
    def total_material_cost(self):
        if self.material and self.material_volume:
            calc_fn = getattr(self.material, "calculate_volume_cost", lambda v: None)
            material_cost = calc_fn(self.material_volume)
            if material_cost is not None:
                return material_cost * self.quantity
        return self.material_cost * self.quantity if self.material_cost else 0.0

    @property
    def total_machining_time(self):
        return sum(op.machining_time for op in self.operations) * self.quantity

    @property
    def total_setup_time(self):
        return sum(getattr(op, 'setup_time', 0) for op in self.operations)

    def total_machining_cost(self, machine_hour_rate=None):
        """Compute machining cost dynamically from user input."""
        rate = machine_hour_rate or 0
        return (self.total_machining_time / 60) * rate

    def total_setup_cost(self, operator_hour_rate=None):
        """Compute setup cost dynamically from user input."""
        rate = operator_hour_rate or 0
        return (self.total_setup_time / 60) * rate

    def total_tooling_cost(self, tool_factor=None):
        """Compute tooling cost dynamically from user input."""
        factor = tool_factor or 1.0
        return sum(op.tooling_cost for op in self.operations) * factor

    def total_cost(self, machine_hour_rate=None, operator_hour_rate=None, tool_factor=None):
        """Dynamic total cost depending on chosen cost rates."""
        return (
            self.total_material_cost +
            self.total_machining_cost(machine_hour_rate) +
            self.total_setup_cost(operator_hour_rate) +
            self.total_tooling_cost(tool_factor)
        )

    def calculate_material_volume(self):
        if self.initial_diameter and self.initial_length:
            radius = self.initial_diameter / 2
            return math.pi * (radius ** 2) * self.initial_length
        elif self.initial_length and self.initial_width and self.initial_height:
            return self.initial_length * self.initial_width * self.initial_height
        return None

    # ----------------------------------------------------------------
    # Serialization
    # ----------------------------------------------------------------
    def to_dict(self, include_operations=True):
        material = self.material.to_dict() if getattr(self, 'material', None) else None
        return {
            'id': self.id,
            'job_id': self.job_id,
            'name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'material': material,
            'material_volume': self.material_volume,
            'total_material_volume': self.total_material_volume,
            'dimensions': {
                'initial': {
                    'length': self.initial_length,
                    'width': self.initial_width,
                    'height': self.initial_height,
                    'diameter': self.initial_diameter
                },
                'final': {
                    'length': self.final_length,
                    'width': self.final_width,
                    'height': self.final_height,
                    'diameter': self.final_diameter
                }
            },
            'operation_count': len(self.operations),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'operations': [op.to_dict() for op in self.operations] if include_operations else []
        }

# -------------------------------------------------------------------
# OPERATION MASTER MODEL
# -------------------------------------------------------------------
class OperationMaster(db.Model):
    __tablename__ = 'Operations'
    
    # Map operation_id from database to id in the model
    id = db.Column('operation_id', db.Integer, primary_key=True)
    operation_name = db.Column('operation_name', db.String(100), nullable=False)
    description = db.Column('description', db.Text)

    # Relationships
    feature_operations = db.relationship('FeatureOperation', back_populates='operation')

    # Add a property to maintain backward compatibility
    @property
    def operation_id(self):
        return self.id

    def to_dict(self):
        return {
            'operation_id': self.id,  # This will use the operation_id from the database
            'operation_name': self.operation_name,
            'description': self.description
        }

# -------------------------------------------------------------------
# PART OPERATION MODEL
# -------------------------------------------------------------------
class PartOperation(db.Model):
    __tablename__ = 'part_operations'

    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id', ondelete='CASCADE'))
    operation_id = db.Column(db.Integer, db.ForeignKey('Operations.operation_id'))
    sequence = db.Column(db.Integer, nullable=True)

    part = db.relationship('Part', back_populates='operations')
    operation = db.relationship('OperationMaster', foreign_keys=[operation_id], backref='part_operations')

    machining_time = db.Column(db.Float, default=0.0)
    machining_cost = db.Column(db.Float, default=0.0)
    tooling_cost = db.Column(db.Float, default=0.0)
    parameters = db.Column(MutableDict.as_mutable(db.JSON), default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'operation_id': self.operation_id,
            'operation_name': self.operation.operation_name if self.operation else None,
            'machining_time': self.machining_time,
            'machining_cost': self.machining_cost,
            'tooling_cost': self.tooling_cost,
            'total_cost': self.machining_cost + self.tooling_cost,
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat()
        }
