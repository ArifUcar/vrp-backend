"""
VRP Data Models
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class Coordinate:
    lat: float
    lng: float

@dataclass
class TimeWindow:
    start: str  # HH:MM format
    end: str    # HH:MM format

@dataclass
class Customer:
    id: str
    name: str
    coordinate: Coordinate
    demand: int
    time_window: Optional[TimeWindow] = None
    service_time: int = 15  # minutes
    priority: int = 5
    special_requirements: List[str] = None

@dataclass
class Vehicle:
    id: str
    name: str
    type: str
    capacity: int
    speed: float = 50.0
    cost_per_km: float = 2.5
    max_distance: Optional[int] = None
    fuel_type: Optional[str] = None
    fuel_consumption: Optional[float] = None
    road_restrictions: List[str] = None
    is_eco_friendly: bool = False
    driver_cost: Optional[float] = None
    maintenance_cost: Optional[float] = None

@dataclass
class VRPRequest:
    depot: Coordinate
    customers: List[Customer]
    vehicles: List[Vehicle]
    max_solving_time: int = 300
    optimization_objective: str = 'balanced'
    use_time_windows: bool = False
    use_capacity_constraints: bool = True
    use_distance_constraints: bool = True
    algorithm: str = 'ortools'

@dataclass
class RouteStop:
    type: str  # 'depot' or 'customer'
    id: str
    name: str
    coordinate: Coordinate
    demand: int = 0
    load: int = 0
    arrival_time: str = '08:00'
    departure_time: str = '08:00'
    service_time: int = 0
    wait_time: int = 0

@dataclass
class Route:
    vehicle_id: str
    vehicle_name: str
    vehicle_type: str
    capacity: int
    stops: List[RouteStop]
    total_distance: float
    total_cost: float
    total_load: int
    total_time: float
    utilization_rate: float
    efficiency: float

@dataclass
class VRPSolution:
    routes: List[Route]
    total_distance: float
    total_cost: float
    total_time: float
    vehicles_used: int
    customers_served: int
    average_utilization: float
    average_efficiency: float
    solving_time: float
    status: str
    algorithm: str
    timestamp: str
