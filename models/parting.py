from .base_operation import BaseOperation


class PartingOperation(BaseOperation):
    """Class for parting operation calculations."""

    def __init__(self, db_params, material_rating, input_dims=None):
        super().__init__(db_params, material_rating)
        self.material_rating = material_rating
        self.diameter = 0.0
        self.depth = 0.0
        self.width = 3.0

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        try:
            self.diameter = float(input_dims.get("diameter"))
            self.depth = float(input_dims.get("depth"))
            self.width = float(input_dims.get("width", 3.0))
        except (TypeError, ValueError) as e:
            raise ValueError("Parting requires valid diameter, depth, and optional width values.") from e

        if self.diameter <= 0 or self.depth <= 0 or self.width <= 0:
            raise ValueError("Diameter, depth, and width must be positive.")

    def _get_machining_parameters(self):
        rough_row, finish_row = self._get_cutting_params()
        rough = self._row_to_cut_dict(rough_row, "rough")
        finish = self._row_to_cut_dict(finish_row, "finish")
        return {
            "feed": finish["feed"] or rough["feed"] or 0.08,
            "spindle_speed": rough["spindle_speed"] or 120.0,
            "depth_of_cut": rough["depth_of_cut"] or self.width,
        }

    def calculate(self, inputs=None):
        try:
            params = self._get_machining_parameters()
            params = self.apply_overrides(params, inputs)

            pass_depth = max(params["depth_of_cut"], self.width)
            passes = max(1, int(-(-self.depth // pass_depth)))
            cutting_distance = self.diameter / 2.0
            feed_rate_mm_min = params["feed"] * params["spindle_speed"]
            time_per_pass = cutting_distance / feed_rate_mm_min
            total_time = (time_per_pass * passes) * 1.15

            machine_hour_rate = getattr(self.params, "machine_hour_rate", 150.0)
            cost = (total_time / 60) * machine_hour_rate

            warnings = []
            if passes > 5:
                warnings.append(f"Multiple parting passes required ({passes}).")
            if params["spindle_speed"] > 250:
                warnings.append("Spindle speed is high for parting; verify rigidity and coolant.")

            return {
                "operation": "parting",
                "total_time_minutes": round(total_time, 3),
                "cost": round(cost, 2),
                "parameters": {
                    "diameter_mm": round(self.diameter, 3),
                    "depth_mm": round(self.depth, 3),
                    "width_mm": round(self.width, 3),
                    "feed_mm_per_rev": round(params["feed"], 3),
                    "spindle_speed_rpm": round(params["spindle_speed"], 0),
                    "passes": passes,
                    "time_per_pass_min": round(time_per_pass, 3),
                },
                "warnings": warnings,
            }
            
        except Exception as e:
            import traceback

            return {"error": f"Error in parting calculation: {str(e)}\n{traceback.format_exc()}"}
