import math
from .base_operation import BaseOperation

class GroovingOperation(BaseOperation):
    """Class for grooving (undercut) operation time and cost estimation."""

    def __init__(self, db_params, material_rating=1.0, input_dims=None):
        super().__init__(db_params, material_rating)
        self.db_params = db_params  # ✅ Add this line

        self.width = 0.0
        self.depth = 0.0

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        try:
            self.width = float(input_dims.get('groove_width') or input_dims['width'])
            self.depth = float(input_dims.get('groove_depth') or input_dims['depth'])
        except (KeyError, ValueError) as e:
            raise ValueError("Both groove_width and groove_depth must be provided as positive numbers.") from e

        if self.width <= 0 or self.depth <= 0:
            raise ValueError("Groove width and depth must be greater than zero.")

    def _get_machining_parameters(self):
        """
        Returns: (rough_params, finish_params) based on notes in db_params
        """
        rough_params, finish_params = {}, {}

        for row in self.db_params:
            note = getattr(row, 'notes', '').strip().lower()
            if 'rough' in note:
                rough_params = {
                    'depth_of_cut': float(getattr(row, 'depth_of_cut_max', 0)),
                    'spindle_speed': float(getattr(row, 'spindle_speed_min', 0)),
                    'feed': float(getattr(row, 'feed_rate_max', 0))
                }
            elif 'finish' in note:
                finish_params = {
                    'depth_of_cut': float(getattr(row, 'depth_of_cut_min', 0)),
                    'spindle_speed': float(getattr(row, 'spindle_speed_max', 0)),
                    'feed': float(getattr(row, 'feed_rate_min', 0))
                }

        if not rough_params or not finish_params:
            raise ValueError("Missing rough or finish cut parameters for grooving.")

        return rough_params, finish_params

    def calculate(self, inputs=None):
        try:
            rough, finish = self._get_machining_parameters()

            # Tool width assumed same as rough DOC
            tool_width = rough['depth_of_cut']
            num_passes = max(1, math.ceil(self.width / tool_width))

            # Assume groove is cut circumferentially (1 rotation per pass)
            circumference = 3.14 * 20  # approx 20 mm dia job assumed, can be enhanced later
            rough_time_per_pass = circumference / (rough['feed'] * rough['spindle_speed'])
            finish_time_per_pass = circumference / (finish['feed'] * finish['spindle_speed'])

            total_rough_time = rough_time_per_pass * num_passes
            total_finish_time = finish_time_per_pass * num_passes

            total_time = (total_rough_time + total_finish_time) * 1.2  # 20% buffer
            self.MACHINE_HOUR_RATE = 150.0
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE

            return{
                'operation': 'grooving',
                'total_time_minutes': round(total_time, 3),
                'cost': round(cost, 2),
                'groove_width': round(self.width, 2),
                'groove_depth': round(self.depth, 2),
                'rough_cut': {
                    'passes': num_passes,
                    'spindle_speed': round(rough['spindle_speed']),
                    'feed': round(rough['feed'], 3),
                    'depth_of_cut': round(rough['depth_of_cut'], 2),
                    'time_per_pass': round(rough_time_per_pass, 3),
                    'total_time': round(total_rough_time, 3)
                },
                'finish_cut': {
                    'passes': num_passes,
                    'spindle_speed': round(finish['spindle_speed']),
                    'feed': round(finish['feed'], 3),
                    'depth_of_cut': round(finish['depth_of_cut'], 2),
                    'time_per_pass': round(finish_time_per_pass, 3),
                    'total_time': round(total_finish_time, 3)
                },
                'warnings': []
            }
    

        except Exception as e:
            import traceback
            return {'error': f"Error in grooving calculation: {str(e)}\n{traceback.format_exc()}"}
