import math
from .base_operation import BaseOperation

class TurningOperation(BaseOperation):
    """Class for turning operation calculations with rough and finish cuts."""

    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Initialize TurningOperation.

        Args:
            db_params (list): List of SQLAlchemy model rows for the selected material_id and operation_id.
                              Each row should include machining parameters and a 'notes' field
                              (e.g., 'Rough cut' or 'Finish cut') to distinguish cut types.

            material_rating (float): Machinability rating of the material (0 to 1). Currently unused,
                                     but retained for future extensions.

            input_dims (dict, optional): Dictionary containing:
                - 'start_diameter' or 'initial_diameter' (float): Starting diameter of the workpiece in mm
                - 'end_diameter' or 'final_diameter' (float): Final diameter after machining in mm
                - 'length' (float): Axial length of the cut in mm
        """

        # Initialize the base class with required parameters
        super().__init__(db_params, material_rating)
        
        # Store parameters
        self.db_params = db_params
        self.material_rating = material_rating
        
        # Initialize dimensions with default values
        self.initial_diameter = 0
        self.final_diameter = 0
        self.length = 0
        
        # Set dimensions if provided
        if input_dims is not None:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Set the turning dimensions from user input."""
        try:
            self.initial_diameter = float(input_dims.get('start_diameter') or input_dims['initial_diameter'])
            self.final_diameter = float(input_dims.get('end_diameter') or input_dims['final_diameter'])
            self.length = float(input_dims['length'])
        except (KeyError, ValueError) as e:
            raise ValueError("start_diameter/end_diameter (or initial_diameter/final_diameter) and length are required and must be numbers.") from e

        if self.initial_diameter <= self.final_diameter:
            raise ValueError("Initial/start diameter must be larger than final/end diameter.")
        if self.length <= 0:
            raise ValueError("Length must be a positive number.")

        input_dims.update({
            'start_diameter': self.initial_diameter,
            'end_diameter': self.final_diameter,
            'initial_diameter': self.initial_diameter,
            'final_diameter': self.final_diameter
        })

    
    def _get_machining_parameters(self):
        """
        Separates rough and finish parameters using the 'notes' field.
        Returns a tuple: (rough_params, finish_params)
        """
        rough_params = {}
        finish_params = {}

        for row in self.db_params:
            note = getattr(row, 'notes', '').strip().lower()
            if note == 'rough cut':
                rough_params = {
                    'depth_of_cut': float(getattr(row, 'depth_of_cut_max', 0)),
                    'spindle_speed': float(getattr(row, 'spindle_speed_min', 0)),
                    'feed': float(getattr(row, 'feed_rate_max', 0))
                }
            elif note == 'finish cut':
                finish_params = {
                    'depth_of_cut': float(getattr(row, 'depth_of_cut_min', 0)),
                    'spindle_speed': float(getattr(row, 'spindle_speed_max', 0)),
                    'feed': float(getattr(row, 'feed_rate_min', 0))
                }

        if not rough_params or not finish_params:
            raise ValueError("Missing machining parameters for rough or finish cut.")

        return rough_params, finish_params
        



    def calculate(self, inputs=None):
        try:
            # Constants
            APPROACH = 5  # mm
            OVERRUN = 5   # mm
            effective_length = self.length + APPROACH + OVERRUN
            radial_reduction = (self.initial_diameter - self.final_diameter) / 2

            # Extract parameters
            rough_params, finish_params = self._get_machining_parameters()
            # Rough Cut Calculations
            rough_doc = rough_params['depth_of_cut']
            rough_radial_reduction = max(0, radial_reduction - finish_params['depth_of_cut'])  # leave for finish
            rough_passes = max(1, math.ceil(rough_radial_reduction / rough_doc))
            rough_time_per_pass = effective_length / (rough_params['spindle_speed'] * rough_params['feed'])
            total_rough_time = rough_time_per_pass * rough_passes

            # Finish Cut Calculations
            finish_doc = finish_params['depth_of_cut']
            finish_passes = 1 if finish_doc > 0 else 0
            finish_time = 0
            if finish_passes:
                finish_time = effective_length / (finish_params['spindle_speed'] * finish_params['feed'])

            # Total time with buffer
            total_cutting_time = (total_rough_time + finish_time) * 1.1  # 10% buffer

            # Optional cost calculation
            self.MACHINE_HOUR_RATE = 150.0  # Could be fetched separately
            cost = (total_cutting_time / 60) * self.MACHINE_HOUR_RATE

            # Warnings
            warnings = []
            if rough_passes > 1:
                warnings.append(f"Multiple rough passes ({rough_passes}) used.")
            if rough_params['feed'] * rough_params['spindle_speed'] > 1000:
                warnings.append(f"Rough cut feed rate is high ({rough_params['feed'] * rough_params['spindle_speed']} mm/min).")
            if finish_params['feed'] * finish_params['spindle_speed'] > 1000:
                warnings.append(f"Finish cut feed rate is high ({finish_params['feed'] * finish_params['spindle_speed']} mm/min).")

            # Final return
            result = {
                'operation': 'turning',
                'total_time_minutes': round(total_cutting_time, 3),
                'rough_cut': {
                    'passes': rough_passes,
                    'depth_per_pass': round(rough_doc, 3),
                    'spindle_speed': round(rough_params['spindle_speed'], 0),
                    'feed': round(rough_params['feed'], 3),
                    'time_per_pass': round(rough_time_per_pass, 3),
                    'total_time': round(total_rough_time, 3)
                },
                'finish_cut': {
                    'passes': finish_passes,
                    'depth': round(finish_doc, 3),
                    'spindle_speed': round(finish_params['spindle_speed'], 0),
                    'feed': round(finish_params['feed'], 3),
                    'time': round(finish_time, 3)
                },
                'effective_length': effective_length,
                'initial_diameter': self.initial_diameter,
                'final_diameter': self.final_diameter,
                'length': self.length,
                'cost': round(cost, 2),
                'warnings': warnings
            }
            return self.attach_decision_support(
                result,
                feed=rough_params['feed'],
                spindle_speed=rough_params['spindle_speed'],
                depth_of_cut=rough_doc,
                passes=rough_passes,
                diameter=self.initial_diameter,
                cut_type='rough',
            )

        except Exception as e:
            import traceback
            return {'error': f'Error in turning calculation: {str(e)}\n{traceback.format_exc()}'}
