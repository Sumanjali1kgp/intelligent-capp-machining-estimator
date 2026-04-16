from .base_operation import BaseOperation


class ThreadingOperation(BaseOperation):
    """Class for threading operation calculations (internal and external)."""

    def __init__(self, db_params, material_rating, input_dims=None):
        super().__init__(db_params, material_rating)
        self.diameter = 0.0
        self.length = 0.0
        self.pitch = 0.0
        self.type = "external"

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Set threading parameters from input."""
        if not input_dims:
            raise ValueError("No dimensions provided")

        diameter = input_dims.get("diameter") or input_dims.get("thread_diameter")
        length = input_dims.get("length") or input_dims.get("thread_length")
        pitch = input_dims.get("pitch") or input_dims.get("thread_pitch")

        missing = []
        if diameter is None:
            missing.append("diameter/thread_diameter")
        if length is None:
            missing.append("length/thread_length")
        if pitch is None:
            missing.append("pitch/thread_pitch")

        if missing:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing)}. Please provide either standard "
                "(diameter, length, pitch) or alternative (thread_diameter, thread_length, thread_pitch) parameters."
            )

        try:
            self.diameter = float(diameter)
            self.length = float(length)
            self.pitch = float(pitch)
            self.type = input_dims.get("type", "external").lower()
            self.threads_per_pass = int(input_dims.get("threads_per_pass") or getattr(self.params, "threading_passes", 7))
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Invalid parameter values. diameter, length, and pitch must be valid numbers. "
                f"Got: diameter={diameter}, length={length}, pitch={pitch}"
            ) from e

        if self.diameter <= 0 or self.length <= 0 or self.pitch <= 0:
            raise ValueError("All dimensions (diameter, length, pitch) must be positive.")
        if self.threads_per_pass <= 0:
            raise ValueError("Threads per pass must be a positive integer.")
        if self.type not in ("internal", "external"):
            raise ValueError("Thread type must be 'internal' or 'external'.")

    def _get_machining_parameters(self):
        """Get feed and spindle speed for threading."""
        rough_row, _ = self._get_cutting_params()
        rough = self._row_to_cut_dict(rough_row, "rough")
        return {
            "feed": self.pitch,
            "spindle_speed": rough["spindle_speed"] or float(getattr(self.params, "spindle_speed_min", 60) or 60),
            "passes": getattr(self, "threads_per_pass", None) or int(getattr(self.params, "threading_passes", 7) or 7),
        }

    def calculate(self, inputs=None):
        try:
            params = self._get_machining_parameters()
            params = self.apply_overrides(params, inputs)
            feed = params["feed"]
            spindle_speed = params["spindle_speed"]
            passes = params["passes"]

            single_pass_time = self.length / (feed * spindle_speed)
            total_time = single_pass_time * passes * 1.1

            self.MACHINE_HOUR_RATE = getattr(self.params, "machine_hour_rate", 150.0)
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE

            warnings = []
            if abs(feed - self.pitch) > 1e-6:
                warnings.append(f"Thread feed ({feed} mm) does not match pitch ({self.pitch} mm).")
            if spindle_speed > 800:
                warnings.append("Spindle speed for threading is unusually high.")

            return{
                "operation": "threading",
                "thread_type": self.type,
                "total_time_minutes": round(total_time, 3),
                "parameters": {
                    "diameter": self.diameter,
                    "length": self.length,
                    "pitch": self.pitch,
                    "passes": passes,
                    "feed": round(feed, 3),
                    "spindle_speed": round(spindle_speed, 0),
                    "time_per_pass": round(single_pass_time, 3),
                },
                "cost": round(cost, 2),
                "warnings": warnings,
            }
            
        except Exception as e:
            import traceback

            return {"error": f"Error in threading calculation: {str(e)}\n{traceback.format_exc()}"}
