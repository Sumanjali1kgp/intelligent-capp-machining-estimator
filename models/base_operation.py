from abc import ABC, abstractmethod


class BaseOperation(ABC):
    """Base class for all machining operations."""

    MACHINE_HOUR_RATE = 1500  # INR per hour
    APPROACH = 10  # mm
    OVERRUN = 10  # mm
    SAFETY_FACTOR = 1.2  # 20% safety factor for time estimation

    def __init__(self, db_params, material_rating):
        """
        Initialize the operation with database parameters and material rating.

        Args:
            db_params: Database parameters for the operation. May be a single SQLAlchemy
                row or a list of rows (rough/finish records).
            material_rating (float): Material machinability rating (0-1)
        """
        self.db_params = db_params
        self.params = self._get_primary_param_row(db_params)
        self.material_rating = material_rating
        self.db_conn = None

        if not hasattr(self, "MACHINE_HOUR_RATE"):
            self.MACHINE_HOUR_RATE = 1500

    @staticmethod
    def _get_primary_param_row(db_params):
        """Return the first parameter row when a list payload is supplied."""
        if isinstance(db_params, (list, tuple)):
            return db_params[0] if db_params else None
        return db_params

    def _get_parameter_rows(self):
        """Always return machining parameters as a list of rows."""
        if isinstance(self.db_params, (list, tuple)):
            return [row for row in self.db_params if row is not None]
        return [self.db_params] if self.db_params is not None else []

    def _get_cutting_params(self, require_finish=False):
        """
        Extract rough and finish rows from the DB payload.

        If only one row exists, it is treated as rough and also reused as finish
        unless ``require_finish`` is explicitly requested.
        """
        rows = self._get_parameter_rows()
        if not rows:
            raise ValueError("No database parameters provided.")

        rough_row = None
        finish_row = None

        for row in rows:
            note = (getattr(row, "notes", "") or "").strip().lower()
            if "rough" in note and rough_row is None:
                rough_row = row
            elif "finish" in note and finish_row is None:
                finish_row = row

        if rough_row is None:
            rough_row = rows[0]

        if finish_row is None:
            if require_finish and len(rows) > 1:
                raise ValueError("Missing finish machining parameters.")
            finish_row = rows[-1] if len(rows) > 1 else rough_row

        return rough_row, finish_row

    @staticmethod
    def _row_to_cut_dict(row, cut_type):
        """Normalize a DB row into depth/feed/spindle values."""
        if row is None:
            return {}

        if cut_type == "finish":
            return {
                "depth_of_cut": float(getattr(row, "depth_of_cut_min", 0) or 0),
                "spindle_speed": float(getattr(row, "spindle_speed_max", 0) or 0),
                "feed": float(getattr(row, "feed_rate_min", 0) or 0),
            }

        return {
            "depth_of_cut": float(getattr(row, "depth_of_cut_max", 0) or 0),
            "spindle_speed": float(getattr(row, "spindle_speed_min", 0) or 0),
            "feed": float(getattr(row, "feed_rate_max", 0) or 0),
        }

    def _get_db_connection(self):
        """Get a database connection, creating it if necessary."""
        if self.db_conn is None:
            try:
                if hasattr(self, "params") and isinstance(self.params, dict) and "db" in self.params:
                    self.db_conn = self.params["db"].engine.raw_connection()
                else:
                    from .. import db

                    self.db_conn = db.engine.raw_connection()
            except Exception as e:
                raise RuntimeError(f"Failed to create database connection: {str(e)}")
        return self.db_conn

    @abstractmethod
    def calculate(self, inputs):
        """Calculate operation parameters."""
        pass

    def _get_cutting_speed(self):
        """Get recommended cutting speed based on material."""
        if self.params is None:
            raise ValueError("No machining parameters available.")
        base_speed = (self.params.spindle_speed_min + self.params.spindle_speed_max) / 2
        return base_speed * self.material_rating

    def _get_feed_rate(self):
        """Get recommended feed rate based on material."""
        if self.params is None:
            raise ValueError("No machining parameters available.")
        base_feed = (self.params.feed_rate_min + self.params.feed_rate_max) / 2
        return base_feed * (0.5 + self.material_rating / 2)

    def _check_limits(self, rpm, feed, depth_of_cut):
        """Check if parameters are within machine limits."""
        if self.params is None:
            return ["No machining limits available"]

        warnings = []
        if rpm > self.params.spindle_speed_max:
            warnings.append(
                f"RPM ({rpm:.0f}) exceeds maximum recommended ({self.params.spindle_speed_max:.0f})"
            )
        if feed > self.params.feed_rate_max:
            warnings.append(
                f"Feed rate ({feed:.2f}) exceeds maximum recommended ({self.params.feed_rate_max:.2f})"
            )
        if depth_of_cut > self.params.depth_of_cut_max:
            warnings.append(
                f"Depth of cut ({depth_of_cut:.2f}mm) exceeds maximum recommended ({self.params.depth_of_cut_max:.2f}mm)"
            )
        return warnings if warnings else ["All parameters within recommended limits"]

    @staticmethod
  
    def apply_overrides(params, inputs):
        """
        Override spindle speed or feed rate with user-provided values.

        Args:
            params (dict): Parameter dictionary (from DB)
            inputs (dict): User inputs from frontend form
        Returns:
            dict: Updated parameter dictionary
        """
        if not inputs:
            return params

        def safe_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        user_feed = safe_float(inputs.get("feed"))
        user_spindle = safe_float(inputs.get("spindle_speed"))

        if user_feed:
            params["feed"] = user_feed
        if user_spindle:
            params["spindle_speed"] = user_spindle

        return params
