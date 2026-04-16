from extensions import db


class MachiningParameter(db.Model):
    """Stores machining parameters for each material-operation combination."""

    __tablename__ = "MachiningParameters"

    param_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    material_id = db.Column(db.Integer, db.ForeignKey("Materials.material_id"), nullable=False)
    operation_id = db.Column(db.Integer, db.ForeignKey("Operations.operation_id"), nullable=False)

    spindle_speed_min = db.Column(db.Float)
    spindle_speed_max = db.Column(db.Float)
    feed_rate_min = db.Column(db.Float)
    feed_rate_max = db.Column(db.Float)
    depth_of_cut_min = db.Column(db.Float)
    depth_of_cut_max = db.Column(db.Float)

    notes = db.Column(db.Text)

    material = db.relationship(
        "Material",
        backref=db.backref("machining_parameters", lazy=True, cascade="all, delete-orphan"),
    )

    operation = db.relationship(
        "OperationMaster",
        backref=db.backref("machining_params", lazy=True, cascade="all, delete-orphan"),
    )

    def to_dict(self):
        """Convert this record into a dict for JSON serialization."""
        return {
            "param_id": self.param_id,
            "material_id": self.material_id,
            "operation_id": self.operation_id,
            "spindle_speed_min": self.spindle_speed_min,
            "spindle_speed_max": self.spindle_speed_max,
            "feed_rate_min": self.feed_rate_min,
            "feed_rate_max": self.feed_rate_max,
            "depth_of_cut_min": self.depth_of_cut_min,
            "depth_of_cut_max": self.depth_of_cut_max,
            "notes": self.notes,
        }

    @staticmethod
    def get_parameters_for_operation(material_id, operation_id):
        """Return all machining parameter rows for a given material and operation."""
        return get_parameters_for_operation(material_id, operation_id)


def get_parameters_for_operation(material_id, operation_id):
    """Module-level helper used by routes and calculators."""
    try:
        return (
            MachiningParameter.query.filter_by(
                material_id=material_id,
                operation_id=operation_id,
            )
            .order_by(MachiningParameter.param_id.asc())
            .all()
        )
    except Exception as e:
        print(f"[MachiningParameter Error] {e}")
        return []
