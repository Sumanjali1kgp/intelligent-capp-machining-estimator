import math
import logging

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)


class DrillingOperation(BaseOperation):
    """Class for drilling operation calculations with peck drilling support."""

    def __init__(self, db_params, material_rating, input_dims=None):
        super().__init__(db_params, material_rating)
        self.material_rating = material_rating
        self.diameter = 0.0
        self.depth = 0.0
        self.peck_depth = 0.0
        self.retract_distance = 2.0

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Set drilling dimensions from input."""
        try:
            self.diameter = float(input_dims.get("diameter") or input_dims.get("hole_diameter"))
            self.depth = float(input_dims.get("depth") or input_dims.get("hole_depth"))
            default_peck = min(3 * self.diameter, 15.0)
            self.peck_depth = float(input_dims.get("peck_depth", default_peck))
            self.retract_distance = max(1.0, min(5.0, float(input_dims.get("retract_distance", 2.0))))
        except (KeyError, ValueError) as e:
            raise ValueError(
                "Both diameter (or hole_diameter) and depth (or hole_depth) must be provided as positive numbers."
            ) from e

        if self.diameter <= 0 or self.depth <= 0 or self.peck_depth <= 0:
            raise ValueError("Diameter, depth, and peck depth must be positive values.")
        if self.peck_depth < self.diameter * 0.5:
            raise ValueError(f"Peck depth ({self.peck_depth}mm) is too small for drill diameter {self.diameter}mm.")
        if self.peck_depth > 20.0:
            raise ValueError(f"Peck depth ({self.peck_depth}mm) exceeds maximum allowed (20mm).")

    def _get_machining_parameters(self):
        """Retrieve feed and spindle speed for drilling."""
        if not self.db_params:
            raise ValueError("No database parameters provided.")

        rough_row, _ = self._get_cutting_params()
        rough = self._row_to_cut_dict(rough_row, "rough")
        feed = rough["feed"] or float(getattr(self.params, "feed_rate_min", 0.1) or 0.1)
        spindle_speed = rough["spindle_speed"] or float(getattr(self.params, "spindle_speed_min", 500) or 500)
        spindle_speed *= (0.5 + (self.material_rating * 0.5))

        return {
            "feed": round(feed, 3),
            "spindle_speed": round(spindle_speed, 1),
        }

    def calculate(self, inputs=None):
        """Calculate drilling time and cost."""
        try:
            params = self._get_machining_parameters()
            params = self.apply_overrides(params, inputs)

            feed = params["feed"]
            spindle_speed = params["spindle_speed"]
            feed_rate_mm_min = feed * spindle_speed
            peck_count = max(1, math.ceil(self.depth / self.peck_depth))
            total_travel = self.depth + (self.retract_distance * (peck_count - 1))
            cutting_time = total_travel / feed_rate_mm_min
            total_time = cutting_time * 1.1

            machine_hour_rate = getattr(self.params, "machine_hour_rate", 150.0)
            cost = (total_time / 60) * machine_hour_rate

            warnings = []
            if feed_rate_mm_min > 1000:
                warnings.append(f"High feed rate: {feed_rate_mm_min:.1f} mm/min")
            if peck_count > 1:
                warnings.append(f"Using {peck_count} pecks with {self.retract_distance}mm retract")
            if self.diameter < 3.0 and feed > 0.1:
                warnings.append("Consider reducing feed rate for small diameter drills")

            return {
                "operation": "drilling",
                "total_time_minutes": round(total_time, 3),
                "cost": round(cost, 2),
                "material_rating": self.material_rating,
                "machine_hour_rate": machine_hour_rate,
                "parameters": {
                    "diameter_mm": round(self.diameter, 2),
                    "depth_mm": round(self.depth, 2),
                    "peck_depth_mm": round(self.peck_depth, 2),
                    "feed_mm_per_rev": round(feed, 3),
                    "spindle_speed_rpm": round(spindle_speed, 1),
                    "feed_rate_mm_per_min": round(feed_rate_mm_min, 1),
                    "peck_count": peck_count,
                    "total_travel_mm": round(total_travel, 2),
                },
                "warnings": warnings,
            }
            
        except Exception as e:
            error_msg = f"Error in drilling calculation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "operation": "drilling",
                "parameters": {
                    "diameter_mm": getattr(self, "diameter", 0),
                    "depth_mm": getattr(self, "depth", 0),
                },
            }
