from extensions import db

class Feature(db.Model):
    __tablename__ = 'features'
    
    feature_id = db.Column(db.Integer, primary_key=True)
    feature_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    operations = db.relationship('FeatureOperation', back_populates='feature', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'feature_id': self.feature_id,
            'feature_name': self.feature_name,
            'description': self.description
        }
        
    def __repr__(self):
        return f"<Feature {self.feature_name}>"
