from extensions import db

class FeatureOperation(db.Model):
    __tablename__ = 'feature_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    feature_id = db.Column(db.Integer, db.ForeignKey('features.feature_id'), nullable=False)
    operation_id = db.Column('operation_id', db.Integer, db.ForeignKey('Operations.operation_id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False, default=1)
    
    # Relationships
    feature = db.relationship('Feature', back_populates='operations')
    operation = db.relationship('OperationMaster', back_populates='feature_operations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'feature_id': self.feature_id,
            'operation_id': self.operation_id,
            'sequence': self.sequence,
            'operation_name': self.operation.operation_name if self.operation else None
        }
        
    def __repr__(self):
        return f"<FeatureOperation feature_id={self.feature_id} operation_id={self.operation_id}>"
