"""
Validation Service
"""
from typing import List, Dict, Any
from models.vrp_models import VRPRequest, Customer, Vehicle, Coordinate

class ValidationService:
    def __init__(self):
        pass
    
    def validate_vrp_request(self, request: VRPRequest) -> List[str]:
        """Validate VRP request data"""
        errors = []
        
        # Validate depot
        if not request.depot:
            errors.append("Depot coordinates are required")
        elif not self._is_valid_coordinate(request.depot):
            errors.append("Invalid depot coordinates")
        
        # Validate customers
        if not request.customers:
            errors.append("At least one customer is required")
        else:
            for i, customer in enumerate(request.customers):
                customer_errors = self._validate_customer(customer, i + 1)
                errors.extend(customer_errors)
        
        # Validate vehicles
        if not request.vehicles:
            errors.append("At least one vehicle is required")
        else:
            for i, vehicle in enumerate(request.vehicles):
                vehicle_errors = self._validate_vehicle(vehicle, i + 1)
                errors.extend(vehicle_errors)
        
        # Validate solving time
        if request.max_solving_time <= 0:
            errors.append("Max solving time must be positive")
        elif request.max_solving_time > 3600:  # 1 hour max
            errors.append("Max solving time cannot exceed 3600 seconds")
        
        # Validate optimization objective
        valid_objectives = ['distance', 'cost', 'time', 'balanced']
        if request.optimization_objective not in valid_objectives:
            errors.append(f"Invalid optimization objective. Must be one of: {valid_objectives}")
        
        # Validate algorithm
        valid_algorithms = ['nearest_neighbor', 'genetic', 'ortools']
        if request.algorithm not in valid_algorithms:
            errors.append(f"Invalid algorithm. Must be one of: {valid_algorithms}")
        
        return errors
    
    def _validate_customer(self, customer: Customer, index: int) -> List[str]:
        """Validate customer data"""
        errors = []
        
        if not customer.id:
            errors.append(f"Customer {index}: ID is required")
        
        if not customer.name:
            errors.append(f"Customer {index}: Name is required")
        
        if not customer.coordinate:
            errors.append(f"Customer {index}: Coordinates are required")
        elif not self._is_valid_coordinate(customer.coordinate):
            errors.append(f"Customer {index}: Invalid coordinates")
        
        if customer.demand <= 0:
            errors.append(f"Customer {index}: Demand must be positive")
        
        if customer.service_time < 0:
            errors.append(f"Customer {index}: Service time cannot be negative")
        
        if customer.priority < 1 or customer.priority > 10:
            errors.append(f"Customer {index}: Priority must be between 1 and 10")
        
        # Validate time window
        if customer.time_window:
            if not self._is_valid_time(customer.time_window.start):
                errors.append(f"Customer {index}: Invalid time window start time")
            if not self._is_valid_time(customer.time_window.end):
                errors.append(f"Customer {index}: Invalid time window end time")
            
            if self._is_valid_time(customer.time_window.start) and self._is_valid_time(customer.time_window.end):
                start_seconds = self._time_to_seconds(customer.time_window.start)
                end_seconds = self._time_to_seconds(customer.time_window.end)
                if start_seconds >= end_seconds:
                    errors.append(f"Customer {index}: Time window start must be before end")
        
        return errors
    
    def _validate_vehicle(self, vehicle: Vehicle, index: int) -> List[str]:
        """Validate vehicle data"""
        errors = []
        
        if not vehicle.id:
            errors.append(f"Vehicle {index}: ID is required")
        
        if not vehicle.name:
            errors.append(f"Vehicle {index}: Name is required")
        
        if not vehicle.type:
            errors.append(f"Vehicle {index}: Type is required")
        
        if vehicle.capacity <= 0:
            errors.append(f"Vehicle {index}: Capacity must be positive")
        
        if vehicle.speed <= 0:
            errors.append(f"Vehicle {index}: Speed must be positive")
        
        if vehicle.cost_per_km <= 0:
            errors.append(f"Vehicle {index}: Cost per km must be positive")
        
        if vehicle.max_distance is not None and vehicle.max_distance <= 0:
            errors.append(f"Vehicle {index}: Max distance must be positive")
        
        if vehicle.fuel_consumption is not None and vehicle.fuel_consumption <= 0:
            errors.append(f"Vehicle {index}: Fuel consumption must be positive")
        
        if vehicle.driver_cost is not None and vehicle.driver_cost < 0:
            errors.append(f"Vehicle {index}: Driver cost cannot be negative")
        
        if vehicle.maintenance_cost is not None and vehicle.maintenance_cost < 0:
            errors.append(f"Vehicle {index}: Maintenance cost cannot be negative")
        
        return errors
    
    def _is_valid_coordinate(self, coord: Coordinate) -> bool:
        """Check if coordinate is valid"""
        if not coord:
            return False
        
        # Check latitude range
        if not (-90 <= coord.lat <= 90):
            return False
        
        # Check longitude range
        if not (-180 <= coord.lng <= 180):
            return False
        
        return True
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Check if time string is valid HH:MM format"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            
            hours = int(parts[0])
            minutes = int(parts[1])
            
            if not (0 <= hours <= 23):
                return False
            
            if not (0 <= minutes <= 59):
                return False
            
            return True
        except:
            return False
    
    def _time_to_seconds(self, time_str: str) -> int:
        """Convert HH:MM time string to seconds"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 3600 + minutes * 60
        except:
            return 0
