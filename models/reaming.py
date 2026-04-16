import logging

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)


class ReamingOperation(BaseOperation):
    """Class for reaming operation calculations."""

    def __init__(self, db_params, material_rating, input_dims=None):
        super().__init__(db_params, material_rating)
        self.material_rating = material_rating
        self.diameter = 0.0
        self.depth = 0.0
        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Extract and validate reaming dimensions."""
        try:
            self.diameter = float(input_dims.get("diameter") or input_dims.get("hole_diameter"))
            self.depth = float(input_dims.get("depth") or input_dims.get("hole_depth"))
        except (KeyError, ValueError):
            raise ValueError("Reaming requires valid hole_diameter and hole_depth values.")
        if self.diameter <= 0 or self.depth <= 0:
            raise ValueError("Diameter and depth must be positive.")

    def _get_machining_parameters(self):
        """Extract reaming parameters from DB rows."""
        _, finish_row = self._get_cutting_params()
        finish = self._row_to_cut_dict(finish_row, "finish")
        feed = finish["feed"] or float(getattr(self.params, "feed_rate_min", 0.1) or 0.1)
        speed = finish["spindle_speed"] or float(getattr(self.params, "spindle_speed_max", 500) or 500)
        return {
            "feed": feed * 0.5,
            "spindle_speed": speed * (0.8 + self.material_rating * 0.2),
        }

    def calculate(self, inputs=None):
        """Compute total time and cost for reaming."""
        try:
            params = self._get_machining_parameters()
            feed = params["feed"]
            speed = params["spindle_speed"]

            feed_rate_mm_min = feed * speed
            cutting_time = self.depth / feed_rate_mm_min
            total_time = cutting_time * 1.1
            cost = (total_time / 60) * getattr(self.params, "machine_hour_rate", 150.0)

            warnings = []
            if self.diameter < 3.0:
                warnings.append("Small reamer diameter may reduce accuracy.")
            if feed_rate_mm_min > 800:
                warnings.append("Feed rate seems high for reaming; check parameters.")

            return {
                "operation": "reaming",
                "total_time_minutes": round(total_time, 3),
                "cost": round(cost, 2),
                "parameters": {
                    "diameter_mm": self.diameter,
                    "depth_mm": self.depth,
                    "feed_mm_rev": feed,
                    "spindle_speed_rpm": speed,
                },
                "warnings": warnings,
            }
            
        except Exception as e:
            logger.error("Error in reaming calculation: %s", e, exc_info=True)
            return {"error": f"Reaming calculation failed: {e}"}
