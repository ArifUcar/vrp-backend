"""
Simple VRP Solver - Fallback for when OR-Tools and Gemini fail
"""
import math
import logging
from typing import Dict, List, Any, Optional
from models.vrp_models import VRPRequest, VRPSolution, Route, RouteStop, Coordinate

logger = logging.getLogger(__name__)

class SimpleVRPService:
    def __init__(self):
        pass
    
    def solve_vrp(self, request: VRPRequest) -> Optional[VRPSolution]:
        """Solve VRP using simple nearest neighbor with forced multi-vehicle"""
        try:
            logger.info(f"Simple VRP solving started for {len(request.customers)} customers, {len(request.vehicles)} vehicles")
            
            # Create routes for each vehicle
            routes = []
            remaining_customers = request.customers.copy()
            
            # Distribute customers evenly among vehicles
            customers_per_vehicle = max(1, len(remaining_customers) // len(request.vehicles))
            
            for vehicle_id, vehicle in enumerate(request.vehicles):
                # Get customers for this vehicle
                vehicle_customers = remaining_customers[:customers_per_vehicle]
                remaining_customers = remaining_customers[customers_per_vehicle:]
                
                # If this is the last vehicle, give it all remaining customers
                if vehicle_id == len(request.vehicles) - 1:
                    vehicle_customers.extend(remaining_customers)
                    remaining_customers = []
                
                if vehicle_customers:
                    route = self._create_simple_route(vehicle_id, vehicle, vehicle_customers, request.depot)
                    routes.append(route)
            
            # Calculate totals
            total_distance = sum(route.total_distance for route in routes)
            total_cost = sum(route.total_cost for route in routes)
            total_time = sum(route.total_time for route in routes)
            customers_served = sum(len([s for s in route.stops if s.type == 'customer']) for route in routes)
            
            # Calculate averages
            average_utilization = sum(route.utilization_rate for route in routes) / len(routes) if routes else 0
            average_efficiency = sum(route.efficiency for route in routes) / len(routes) if routes else 0
            
            solution = VRPSolution(
                routes=routes,
                total_distance=round(total_distance, 2),
                total_cost=round(total_cost, 2),
                total_time=round(total_time, 2),
                vehicles_used=len(routes),
                customers_served=customers_served,
                average_utilization=round(average_utilization * 100, 1),
                average_efficiency=round(average_efficiency, 2),
                solving_time=0.01,  # Very fast
                status='success',
                algorithm='Simple Multi-Vehicle',
                timestamp='2025-01-01T00:00:00'
            )
            
            logger.info(f"Simple VRP solution created: {len(routes)} vehicles, {customers_served} customers")
            return solution
            
        except Exception as e:
            logger.error(f"Simple VRP solving error: {str(e)}")
            return None
    
    def _create_simple_route(self, vehicle_id: int, vehicle, customers: List, depot: Coordinate) -> Route:
        """Create a simple route using nearest neighbor"""
        route = Route(
            vehicle_id=f'V{vehicle_id + 1:03d}',
            vehicle_name=vehicle.name,
            vehicle_type=vehicle.type,
            capacity=vehicle.capacity,
            stops=[],
            total_distance=0,
            total_cost=0,
            total_load=0,
            total_time=0,
            utilization_rate=0,
            efficiency=0
        )
        
        # Start at depot
        current_location = depot
        route.stops.append(RouteStop(
            type='depot',
            id='DEPOT',
            name='Depo',
            coordinate=depot,
            load=0,
            arrival_time='08:00',
            departure_time='08:00',
            service_time=0
        ))
        
        # Visit customers using nearest neighbor
        remaining_customers = customers.copy()
        current_time = 8 * 60  # 08:00 in minutes
        
        while remaining_customers:
            # Find nearest customer
            nearest_customer = None
            min_distance = float('inf')
            
            for customer in remaining_customers:
                distance = self._calculate_distance(current_location, customer.coordinate)
                if distance < min_distance:
                    min_distance = distance
                    nearest_customer = customer
            
            if nearest_customer:
                # Add customer to route
                route.stops.append(RouteStop(
                    type='customer',
                    id=nearest_customer.id,
                    name=nearest_customer.name,
                    coordinate=nearest_customer.coordinate,
                    demand=nearest_customer.demand,
                    load=route.total_load + nearest_customer.demand,
                    arrival_time=self._minutes_to_time(current_time),
                    departure_time=self._minutes_to_time(current_time + nearest_customer.service_time),
                    service_time=nearest_customer.service_time,
                    wait_time=0
                ))
                
                # Update route metrics
                route.total_distance += min_distance
                route.total_load += nearest_customer.demand
                current_time += nearest_customer.service_time + int(min_distance * 60 / 50)  # 50 km/h
                current_location = nearest_customer.coordinate
                
                # Remove from remaining
                remaining_customers.remove(nearest_customer)
        
        # Return to depot
        return_distance = self._calculate_distance(current_location, depot)
        route.total_distance += return_distance
        current_time += int(return_distance * 60 / 50)
        
        route.stops.append(RouteStop(
            type='depot',
            id='DEPOT',
            name='Depo',
            coordinate=depot,
            load=route.total_load,
            arrival_time=self._minutes_to_time(current_time),
            departure_time=self._minutes_to_time(current_time),
            service_time=0
        ))
        
        # Calculate final metrics
        route.total_cost = route.total_distance * vehicle.cost_per_km
        route.total_time = route.total_distance / 50  # hours at 50 km/h
        route.utilization_rate = route.total_load / route.capacity if route.capacity > 0 else 0
        route.efficiency = route.total_load / route.total_distance if route.total_distance > 0 else 0
        
        return route
    
    def _calculate_distance(self, coord1: Coordinate, coord2: Coordinate) -> float:
        """Calculate Haversine distance between two coordinates"""
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(coord1.lat), math.radians(coord1.lng)
        lat2, lon2 = math.radians(coord2.lat), math.radians(coord2.lng)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes to HH:MM time string"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

