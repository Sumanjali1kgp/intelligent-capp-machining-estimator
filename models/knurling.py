from .base_operation import BaseOperation


class KnurlingOperation(BaseOperation):
    """Class for knurling operation calculations."""

    def __init__(self, db_params, material_rating, input_dims=None):
        super().__init__(db_params, material_rating)
        self.material_rating = material_rating
        self.knurling_length = 0.0
        self.workpiece_diameter = 0.0

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        try:
            self.knurling_length = float(input_dims.get("knurling_length") or input_dims.get("length"))
            self.workpiece_diameter = float(input_dims.get("workpiece_diameter") or input_dims.get("diameter"))
        except Exception as e:
            raise ValueError("Both length and diameter are required for knurling and must be valid numbers.") from e

        if self.knurling_length <= 0 or self.workpiece_diameter <= 0:
            raise ValueError("Length and diameter must be positive numbers.")

    def _get_machining_parameters(self):
        """Separate rough and finish parameters and select intelligently."""
        rough_row, finish_row = self._get_cutting_params()
        rough_params = self._row_to_cut_dict(rough_row, "rough")
        finish_params = self._row_to_cut_dict(finish_row, "finish")
        return rough_params, finish_params

    def calculate(self, inputs=None):
        try:
            rough_params, finish_params = self._get_machining_parameters()

            passes = 2
            time_per_pass_rough = self.knurling_length / (rough_params["spindle_speed"] * rough_params["feed"])
            time_per_pass_finish = self.knurling_length / (finish_params["spindle_speed"] * finish_params["feed"])
            total_time = (time_per_pass_rough + time_per_pass_finish) * passes * 1.1

            machine_hour_rate = 150.0
            cost = (total_time / 60) * machine_hour_rate

            warnings = []
            if rough_params == finish_params:
                warnings.append("Finish knurling parameters missing; rough parameters reused.")
            if rough_params["spindle_speed"] > 200:
                warnings.append("Rough cut spindle speed is high for knurling.")
            if rough_params["feed"] > 0.5:
                warnings.append("Rough feed rate is high; may damage knurling tool.")

            return{
                "operation": "knurling",
                "total_time_minutes": round(total_time, 3),
                "cost": round(cost, 2),
                "material_rating": self.material_rating,
                "parameters": {
                    "knurling_length_mm": round(self.knurling_length, 3),
                    "workpiece_diameter_mm": round(self.workpiece_diameter, 3),
                    "rough": rough_params,
                    "finish": finish_params,
                    "passes": passes,
                },
                "warnings": warnings,
            }
            
        except Exception as e:
            import traceback

            return {"error": f"Error in knurling calculation: {str(e)}\n{traceback.format_exc()}"}
