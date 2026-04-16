# Standard library imports
import os
import sys

# Third-party imports
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from models import (
    TurningOperation, FacingOperation, 
    DrillingOperation, MillingOperation
)

class MachiningCalculator:
    """
    Main calculator class that delegates to specific operation classes.
    This follows the Strategy design pattern where each operation is a strategy.
    """
    
    def __init__(self, db_params, material_rating, operation_id, material_id=None, user_inputs=None):
        """
        Initializes the calculator with parameters from the database.
        
        Args:
            db_params (MachiningParameter): The SQLAlchemy object with machining parameters.
            material_rating (float): The machinability rating of the material (0-1).
            operation_id (int): The ID of the operation in the database.
            material_id (int, optional): The ID of the material in the database.
            user_inputs (dict, optional): Dictionary containing user inputs like dimensions.
        """
        self.params = db_params
        self.material_rating = material_rating
        self.operation_id = operation_id
        self.material_id = material_id
        self.user_inputs = user_inputs 
        self.operations ={
            'turning': TurningOperation(db_params, material_rating),
            'facing': FacingOperation(db_params, material_rating),
            'drilling': DrillingOperation(db_params, material_rating),
            'milling': MillingOperation(db_params, material_rating)
        }


    def calculate_machining_parameters(self, operation_name, user_inputs=None):
        """
        Calculate all machining parameters including time and cost.
        
        Args:
            operation_name (str): Name of the operation (e.g., 'turning', 'facing')
            user_inputs (dict, optional): Dictionary containing user inputs like dimensions.
            
        Returns:
            dict: Dictionary containing calculated parameters
        """
        op_name = operation_name.lower()
        
        if op_name not in self.operations:
            raise ValueError(f"Unsupported operation: {operation_name}")
            
        # Delegate to the appropriate operation handler
        operation = self.operations[op_name]
        return operation.calculate(self.user_inputs)

    def calculate_time(self, operation_name, user_inputs=None):
        """
        Calculate the machining time for a specific operation.
        
        Args:
            operation_name (str): Name of the operation
            user_inputs (dict): Dictionary containing user inputs like dimensions.            
        Returns:
tuple: A tuple containing the raw machining time and total time
        """
        result = self.calculate_machining_parameters(operation_name, user_inputs )
        if 'error' in result:
            raise ValueError(result['error'])
            
        machining_time = result.get('machining_time', 0)
        total_time = machining_time * (1 + self.material_rating * 0.1)  # Add material factor
        
        return machining_time, total_time
