import math
import logging

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)


class BoringOperation(BaseOperation):
    """Class for boring operation calculations with rough and finish cuts."""

    def __init__(self, db_params, material_rating, input_dims=None):
        super().__init__(db_params, material_rating)
        self.material_rating = material_rating
        self.initial_diameter = 0.0
        self.final_diameter = 0.0
        self.depth = 0.0

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Set bore dimensions from input."""
        try:
            initial_diameter = input_dims.get("initial_diameter") or input_dims.get("hole_diameter")
            depth = input_dims.get("depth") or input_dims.get("hole_depth")

            if "final_diameter" in input_dims:
                final_diameter = input_dims["final_diameter"]
            elif "hole_diameter" in input_dims and "cutting_depth" in input_dims:
                final_diameter = input_dims["hole_diameter"] + 2 * float(input_dims["cutting_depth"])
            else:
                raise KeyError("Missing required parameters")

            self.initial_diameter = float(initial_diameter)
            self.final_diameter = float(final_diameter)
            self.depth = float(depth)
        except (KeyError, ValueError) as e:
            raise ValueError(
                "Must provide either (initial_diameter, final_diameter, depth) or (hole_diameter, hole_depth, cutting_depth)."
            ) from e

        if self.initial_diameter <= 0 or self.final_diameter <= 0:
            raise ValueError("Diameters must be positive numbers.")
        if self.initial_diameter >= self.final_diameter:
            raise ValueError("Final diameter must be greater than initial diameter.")
        if self.depth <= 0:
            raise ValueError("Depth must be a positive number.")

    def _get_machining_parameters(self, cut_type="rough"):
        """Retrieve machining parameters based on cut type."""
        if not self.db_params:
            raise ValueError("No database parameters provided.")

        rough_row, finish_row = self._get_cutting_params()
        source_row = rough_row if cut_type == "rough" else finish_row
        params = self._row_to_cut_dict(source_row, cut_type)

        if params["spindle_speed"] > 0:
            params["spindle_speed"] *= (0.5 + (self.material_rating * 0.5))

        return params

    def calculate(self, inputs=None):
        """Calculate boring operation time and cost."""
        try:
            diameter_increase = self.final_diameter - self.initial_diameter
            if diameter_increase <= 0:
                raise ValueError("Final diameter must be greater than initial diameter.")

            radial_increase = diameter_increase / 2
            rough_params = self._get_machining_parameters("rough")
            finish_params = self._get_machining_parameters("finish")
            rough_params = self.apply_overrides(rough_params, inputs)
            finish_params = self.apply_overrides(finish_params, inputs)

            finish_doc = min(finish_params["depth_of_cut"], radial_increase)
            rough_depth_total = max(0, radial_increase - finish_doc)

            max_rough_doc = max(rough_params["depth_of_cut"], 0.1)
            rough_passes = max(1, int(math.ceil(rough_depth_total / max_rough_doc)))
            actual_rough_doc = rough_depth_total / rough_passes if rough_passes > 0 else 0

            feed_rate_rough = rough_params["feed"] * rough_params["spindle_speed"]
            rough_time_per_pass = self.depth / feed_rate_rough if feed_rate_rough > 0 else 0
            total_rough_time = rough_time_per_pass * rough_passes

            finish_time = 0
            feed_rate_finish = finish_params["feed"] * finish_params["spindle_speed"]
            if finish_doc > 0 and feed_rate_finish > 0:
                finish_time = self.depth / feed_rate_finish

            total_cutting_time = (total_rough_time + finish_time) * 1.1
            machine_hour_rate = getattr(self.params, "machine_hour_rate", 150.0)
            cost = (total_cutting_time / 60) * machine_hour_rate

            warnings = []
            if rough_passes > 3:
                warnings.append(f"High number of roughing passes ({rough_passes}) - consider increasing depth of cut.")
            if rough_passes > 10:
                warnings.append("Too many rough passes; consider revisiting DOC selection.")
            if feed_rate_rough > 1000:
                warnings.append(f"High rough cut feed rate: {feed_rate_rough:.1f} mm/min")
            if finish_doc > 0 and feed_rate_finish > 800:
                warnings.append("High finish cut feed rate.")
            if actual_rough_doc < 0.1:
                warnings.append("Very small roughing depth of cut - consider adjusting parameters.")

            return {
                "operation": "boring",
                "total_time_minutes": round(total_cutting_time, 3),
                "material_rating": self.material_rating,
                "machine_hour_rate": machine_hour_rate,
                "rough_cut": {
                    "passes": rough_passes,
                    "depth_per_pass_mm": round(actual_rough_doc, 3),
                    "feed_mm_per_rev": round(rough_params["feed"], 3),
                    "spindle_speed_rpm": round(rough_params["spindle_speed"], 0),
                    "feed_rate_mm_per_min": round(feed_rate_rough, 1),
                    "time_per_pass_min": round(rough_time_per_pass, 3),
                    "total_time_min": round(total_rough_time, 3),
                },
                "finish_cut": {
                    "depth_mm": round(finish_doc, 3),
                    "feed_mm_per_rev": round(finish_params["feed"], 3),
                    "spindle_speed_rpm": round(finish_params["spindle_speed"], 0),
                    "feed_rate_mm_per_min": round(feed_rate_finish, 1),
                    "time_min": round(finish_time, 3),
                },
                "cost": round(cost, 2),
                "warnings": warnings,
            }
           
        except Exception as e:
            error_msg = f"Error in boring calculation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "operation": "boring",
                "parameters": {
                    "initial_diameter_mm": getattr(self, "initial_diameter", 0),
                    "final_diameter_mm": getattr(self, "final_diameter", 0),
                    "depth_mm": getattr(self, "depth", 0),
                },
            }
