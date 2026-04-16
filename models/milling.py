import math
from .base_operation import BaseOperation

class MillingOperation(BaseOperation):
    """Class for milling operation calculations."""
    
    def calculate(self, inputs):
        """
        Calculate milling operation parameters.
        
        Args:
            inputs (dict): Dictionary containing:
                - width (float): Width of cut in mm
                - length (float): Length of cut in mm
                - depth (float): Depth of cut per pass in mm
                - total_depth (float, optional): Total depth to remove in mm
                - tool_diameter (float, optional): Cutter diameter in mm (default: 10mm)
                
        Returns:
            dict: Dictionary containing all calculated parameters
        """
        try:
            width = float(inputs.get('width', 0))
            length = float(inputs.get('length', 0))
            depth = float(inputs.get('depth', self.params.depth_of_cut_min))
            
            if width <= 0 or length <= 0 or depth <= 0:
                raise ValueError("All dimensions must be positive")
            
            # Get recommended parameters
            cutting_speed = self._get_cutting_speed()
            feed = self._get_feed_rate()
            
            # Tool parameters
            tool_diameter = float(inputs.get('tool_diameter', 10))  # default 10mm
            num_teeth = 2  # Default number of teeth
            
            # RPM calculation
            rpm = (cutting_speed * 1000) / (math.pi * tool_diameter)
            
            # Calculate feed per tooth and effective feed rate
            feed_per_tooth = feed / num_teeth
            effective_feed = feed_per_tooth * num_teeth * rpm
            
            # Milling time (minutes)
            time_per_pass = (length + self.APPROACH + self.OVERRUN) / effective_feed
            
            # Number of passes based on depth
            total_depth = float(inputs.get('total_depth', depth))
            num_passes = max(1, math.ceil(total_depth / depth))
            
            total_time = time_per_pass * num_passes
            
            # Calculate cost
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE
            
            return {
                'operation': 'milling',
                'cutting_speed': round(cutting_speed, 2),
                'feed_rate': round(feed, 3),
                'rpm': round(rpm, 2),
                'depth_of_cut': round(depth, 2),
                'machining_time': round(total_time, 2),
                'cost': round(cost, 2),
                'num_passes': num_passes,
                'tool_diameter': tool_diameter,
                'warnings': self._check_limits(rpm, feed, depth)
            }
            
        except (ValueError, TypeError) as e:
            return {'error': f'Invalid input parameters: {str(e)}'}
