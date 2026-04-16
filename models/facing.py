import math
import logging
from datetime import datetime

from .base_operation import BaseOperation

logger = logging.getLogger(__name__)


class FacingOperation(BaseOperation):
    """Calculate facing operation time and cost with rough, semi-finish, and finish stages."""

    def __init__(self, db_params, material_rating, input_dims=None):
        super().__init__(db_params, material_rating)
        self.material_rating = material_rating
        self.diameter = 0.0
        self.depth_of_cut = 0.0
        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Set diameter and depth of cut."""
        self.diameter = float(input_dims.get("diameter", 0))
        self.depth_of_cut = float(input_dims.get("depth_of_cut", 0))
        if self.diameter <= 0 or self.depth_of_cut <= 0:
            raise ValueError("Diameter and depth_of_cut must be positive numbers.")

    @staticmethod
    def _safe_float(value, default):
        """Safely convert to float, use default if blank or invalid."""
        try:
            parsed = float(value)
            return parsed if parsed > 0 else default
        except (TypeError, ValueError):
            return default

    def _get_machining_parameters(self):
        """Retrieve rough and finish parameters with sensible fallbacks."""
        rough_row, finish_row = self._get_cutting_params()
        rough = self._row_to_cut_dict(rough_row, "rough")
        finish = self._row_to_cut_dict(finish_row, "finish")
        return {
            "rough_feed": rough["feed"] or 0.16,
            "finish_feed": finish["feed"] or rough["feed"] or 0.12,
            "rough_speed": rough["spindle_speed"] or 170.0,
            "finish_speed": finish["spindle_speed"] or rough["spindle_speed"] or 285.0,
            "rough_doc": rough["depth_of_cut"] or 1.85,
            "finish_doc": finish["depth_of_cut"] or 0.05,
            "machine_hour_rate": float(getattr(self.params, "machine_hour_rate", 150.0)),
        }

    def calculate(self, inputs=None):
        """Perform time and cost calculation for facing with 3 stages."""
        params = self._get_machining_parameters()

        if inputs:
            params["rough_feed"] = self._safe_float(inputs.get("feed"), params["rough_feed"])
            params["finish_feed"] = self._safe_float(inputs.get("feed"), params["finish_feed"])
            params["rough_speed"] = self._safe_float(inputs.get("spindle_speed"), params["rough_speed"])
            params["finish_speed"] = self._safe_float(inputs.get("spindle_speed"), params["finish_speed"])

        length_of_cut = self.diameter / 2.0

        semi_feed = (params["rough_feed"] + params["finish_feed"]) / 2.0
        semi_speed = (params["rough_speed"] + params["finish_speed"]) / 2.0
        semi_doc = (params["rough_doc"] + params["finish_doc"]) / 2.0

        total_rough_depth = max(0, self.depth_of_cut - semi_doc - params["finish_doc"])
        rough_passes = math.ceil(total_rough_depth / params["rough_doc"]) if params["rough_doc"] else 0
        actual_rough_doc = total_rough_depth / rough_passes if rough_passes else 0

        rough_time_per_pass = length_of_cut / (params["rough_feed"] * params["rough_speed"])
        rough_time = rough_time_per_pass * rough_passes
        semi_time = length_of_cut / (semi_feed * semi_speed)
        finish_time = length_of_cut / (params["finish_feed"] * params["finish_speed"])

        total_time = (rough_time + semi_time + finish_time) * 1.1
        cost = (total_time / 60.0) * params["machine_hour_rate"]

        warnings = [
            f"{rough_passes} rough passes",
            "1 semi-finish pass",
            "1 finish pass",
        ]
        if rough_passes > 10:
            warnings.append("Too many rough passes; consider increasing depth of cut.")

        return {
            "operation": "facing",
            "total_time_minutes": round(total_time, 3),
            "rough_cut": {
                "passes": rough_passes,
                "depth_per_pass": round(actual_rough_doc, 3),
                "spindle_speed": params["rough_speed"],
                "feed": params["rough_feed"],
                "time_per_pass": round(rough_time_per_pass, 3),
                "total_time": round(rough_time, 3),
            },
            "semi_finish_cut": {
                "passes": 1,
                "depth": round(semi_doc, 3),
                "spindle_speed": round(semi_speed, 3),
                "feed": round(semi_feed, 3),
                "time": round(semi_time, 3),
            },
            "finish_cut": {
                "passes": 1,
                "depth": round(params["finish_doc"], 3),
                "spindle_speed": params["finish_speed"],
                "feed": params["finish_feed"],
                "time": round(finish_time, 3),
            },
            "cost": round(cost, 2),
            "warnings": warnings,
            "material": getattr(getattr(self.params, "material", None), "material_name", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "machine_hour_rate": params["machine_hour_rate"],
        }
        