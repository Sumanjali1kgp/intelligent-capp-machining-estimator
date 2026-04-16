from extensions import db
from sqlalchemy.orm import validates

class Material(db.Model):
    """Material model storing physical properties and cost metrics."""
    __tablename__ = 'Materials'
    
    material_id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(100), nullable=False, unique=True)
    material_grade = db.Column(db.String(50))
    material_type = db.Column(db.String(50))  # e.g., 'Steel', 'Aluminum', 'Plastic'
    hardness = db.Column(db.Float)            # Hardness in Brinell or Rockwell
    density = db.Column(db.Float)             # Density in g/cm³
    cost_per_kg = db.Column(db.Float)         # Cost per kilogram
    machinability_rating = db.Column(db.Float)  # 0–100 scale
    recommended_tool = db.Column(db.String(100))
    notes = db.Column(db.Text)

    # Relationship to Part table
    parts = db.relationship('Part', backref='material', lazy=True)

    # -------------------------------
    # Validation and computed fields
    # -------------------------------
    @validates('material_name')
    def validate_material_name(self, key, name):
        if not name or not name.strip():
            raise ValueError("Material name cannot be empty")
        return name.strip()

    @validates('cost_per_kg', 'density', 'hardness', 'machinability_rating')
    def validate_positive_values(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    @property
    def cost_per_cm3(self):
        """Compute cost per cubic centimeter from density and cost per kg."""
        if self.density and self.cost_per_kg:
            return (self.cost_per_kg * self.density) / 1000  # Convert g/cm³ → kg/cm³
        return None

    def calculate_volume_cost(self, volume_cm3):
        """Compute cost for a given material volume (cm³)."""
        if self.cost_per_cm3 is not None:
            return self.cost_per_cm3 * volume_cm3
        return None

    def to_dict(self):
        """Convert material attributes to dict for JSON serialization."""
        return {
            'material_id': self.material_id,
            'material_name': self.material_name,
            'material_grade': self.material_grade,
            'material_type': self.material_type,
            'hardness': self.hardness,
            'density': self.density,
            'cost_per_kg': self.cost_per_kg,
            'cost_per_cm3': self.cost_per_cm3,
            'machinability_rating': self.machinability_rating,
            'recommended_tool': self.recommended_tool,
            'notes': self.notes
        }
