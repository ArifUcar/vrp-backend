"""
VRP Solving Service
"""
import time
import math
import logging
from typing import Dict, List, Any, Optional
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from models.vrp_models import VRPRequest, VRPSolution, Route, RouteStop, Coordinate

logger = logging.getLogger(__name__)

class VRPService:
    def __init__(self):
        self.default_cost_per_km = 2.5
        self.default_service_time = 15  # minutes
    
    def solve_vrp(self, request: VRPRequest) -> Optional[VRPSolution]:
        """Solve VRP problem using OR-Tools"""
        start_time = time.time()
        logger.info("Starting VRP solving")
        
        try:
            # Create data model
            data = self._create_data_model(request)
            
            # Solve with OR-Tools
            result = self._solve_with_ortools(data, request)
            
            solving_time = time.time() - start_time
            logger.info(f"VRP solving completed in {solving_time:.2f} seconds")
            
            if result:
                return self._format_solution(result, request, solving_time)
            else:
                logger.warning("No solution found")
                return None
                
        except Exception as e:
            logger.error(f"VRP solving error: {str(e)}")
            return None
    
    def _create_data_model(self, request: VRPRequest) -> Dict[str, Any]:
        """Create data model for OR-Tools"""
        logger.info(f"Creating data model for {len(request.customers)} customers and {len(request.vehicles)} vehicles")
        
        # Distance matrix
        locations = [request.depot] + [customer.coordinate for customer in request.customers]
        distance_matrix = []
        time_matrix = []
        
        for i in range(len(locations)):
            distance_row = []
            time_row = []
            for j in range(len(locations)):
                if i == j:
                    distance_row.append(0)
                    time_row.append(0)
                else:
                    distance = self._calculate_distance(locations[i], locations[j])
                    distance_row.append(int(distance * 1000))  # meters
                    time_row.append(int(distance * 3600 / 50))  # seconds (50 km/h)
            distance_matrix.append(distance_row)
            time_matrix.append(time_row)
        
        # Time windows
        time_windows = []
        if request.use_time_windows:
            time_windows = [(0, 86400)]  # Depot: 24 hours
            for customer in request.customers:
                if customer.time_window:
                    start_time = self._time_to_seconds(customer.time_window.start)
                    end_time = self._time_to_seconds(customer.time_window.end)
                    time_windows.append((start_time, end_time))
                else:
                    time_windows.append((0, 86400))
        
        data = {
            'distance_matrix': distance_matrix,
            'time_matrix': time_matrix,
            'num_vehicles': len(request.vehicles),
            'depot': 0,
            'demands': [0] + [customer.demand for customer in request.customers],
            'vehicle_capacities': [vehicle.capacity for vehicle in request.vehicles],
            'time_windows': time_windows,
            'service_times': [0] + [customer.service_time * 60 for customer in request.customers],
            'vehicle_speeds': [vehicle.speed for vehicle in request.vehicles],
            'vehicle_costs': [vehicle.cost_per_km for vehicle in request.vehicles],
            'vehicle_fixed_costs': [vehicle_id for vehicle_id in range(len(request.vehicles))]  # Different fixed costs
        }
        
        logger.info(f"Data model created: {len(distance_matrix)}x{len(distance_matrix[0])} distance matrix")
        return data
    
    def _solve_with_ortools(self, data: Dict[str, Any], request: VRPRequest) -> Optional[Any]:
        """Solve VRP using OR-Tools"""
        try:
            # Routing Index Manager
            manager = pywrapcp.RoutingIndexManager(
                len(data['distance_matrix']), 
                data['num_vehicles'], 
                data['depot']
            )
            
            # Routing Model
            routing = pywrapcp.RoutingModel(manager)
            
            # Distance callback
            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return data['distance_matrix'][from_node][to_node]
            
            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # Capacity constraint
            def demand_callback(from_index):
                from_node = manager.IndexToNode(from_index)
                return data['demands'][from_node]
            
            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,  # null capacity slack
                data['vehicle_capacities'],  # vehicle maximum capacities
                True,  # start cumul to zero
                'Capacity'
            )
            
            # Time window constraint
            if request.use_time_windows and 'time_windows' in data:
                def time_callback(from_index, to_index):
                    from_node = manager.IndexToNode(from_index)
                    to_node = manager.IndexToNode(to_index)
                    return data['time_matrix'][from_node][to_node] + data['service_times'][from_node]
                
                time_callback_index = routing.RegisterTransitCallback(time_callback)
                routing.AddDimension(
                    time_callback_index,
                    86400,  # maximum time per vehicle (24 hours)
                    86400,  # maximum time per vehicle (24 hours)
                    False,  # don't start cumul to zero
                    'Time'
                )
                time_dimension = routing.GetDimensionOrDie('Time')
                
                # Time window constraints
                for node_idx, time_window in enumerate(data['time_windows']):
                    index = manager.NodeToIndex(node_idx)
                    time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
            
            # Search parameters - optimized for multiple vehicles
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            
            # Use simple strategy for all cases
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC
            )
            search_parameters.time_limit.seconds = min(request.max_solving_time, 30)
            
            search_parameters.solution_limit = 1  # Stop after first solution
            search_parameters.log_search = False  # Disable logging for speed
            
            # Force multiple vehicles by setting different fixed costs
            # Use small fixed cost differences to encourage using different vehicles
            for vehicle_id in range(data['num_vehicles']):
                # Small fixed cost difference to encourage using different vehicles
                fixed_cost = vehicle_id * 1  # 0, 1, 2, 3...
                routing.SetFixedCostOfVehicle(vehicle_id, fixed_cost)
            
            # Solve
            solution = routing.SolveWithParameters(search_parameters)
            
            if solution:
                logger.info(f"Solution found with {data['num_vehicles']} vehicles")
                
                # Check which vehicles are actually used
                used_vehicles = []
                for vehicle_id in range(data['num_vehicles']):
                    index = routing.Start(vehicle_id)
                    if not routing.IsEnd(index):
                        next_index = solution.Value(routing.NextVar(index))
                        if not routing.IsEnd(next_index):
                            used_vehicles.append(vehicle_id)
                
                logger.info(f"Vehicles actually used: {used_vehicles}")
                
                return {
                    'solution': solution,
                    'manager': manager,
                    'routing': routing,
                    'data': data
                }
            else:
                logger.warning(f"No solution found for {data['num_vehicles']} vehicles, {len(data['demands'])-1} customers")
                logger.warning(f"Total demand: {sum(data['demands'])}, Vehicle capacities: {data['vehicle_capacities']}")
                return None
                
        except Exception as e:
            logger.error(f"OR-Tools solving error: {str(e)}")
            return None
    
    def _format_solution(self, result: Dict[str, Any], request: VRPRequest, solving_time: float) -> VRPSolution:
        """Format OR-Tools solution"""
        solution = result['solution']
        manager = result['manager']
        routing = result['routing']
        data = result['data']
        
        routes = []
        total_distance = 0
        total_cost = 0
        total_load = 0
        total_time = 0
        
        for vehicle_id in range(data['num_vehicles']):
            route = self._create_route(vehicle_id, solution, manager, routing, data, request)
            
            # Sadece müşteri içeren rotaları ekle
            customer_stops = [s for s in route.stops if s.type == 'customer']
            if len(customer_stops) > 0:
                routes.append(route)
                total_distance += route.total_distance
                total_cost += route.total_cost
                total_load += route.total_load
                total_time += route.total_time
        
        # Overall metrics
        customers_served = sum(len([s for s in route.stops if s.type == 'customer']) for route in routes)
        # Tüm rotalar aktif (müşteri içeren)
        average_utilization = sum(route.utilization_rate for route in routes) / len(routes) if routes else 0
        average_efficiency = sum(route.efficiency for route in routes) / len(routes) if routes else 0
        
        return VRPSolution(
            routes=routes,
            total_distance=round(total_distance, 2),
            total_cost=round(total_cost, 2),
            total_time=round(total_time, 2),
            vehicles_used=len(routes),  # Sadece müşteri içeren rotaları say
            customers_served=customers_served,
            average_utilization=round(average_utilization * 100, 1),
            average_efficiency=round(average_efficiency, 2),
            solving_time=round(solving_time, 2),
            status='success',
            algorithm='OR-Tools',
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S')
        )
    
    def _create_route(self, vehicle_id: int, solution: Any, manager: Any, routing: Any, data: Dict[str, Any], request: VRPRequest) -> Route:
        """Create a single route from solution"""
        vehicle = request.vehicles[vehicle_id]
        
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
        
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_load = 0
        route_time = 0
        current_time = 0  # Start at 08:00
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            
            if node_index == 0:  # Depot
                stop = RouteStop(
                    type='depot',
                    id='DEPOT',
                    name='Depo',
                    coordinate=request.depot,
                    load=route_load,
                    arrival_time=self._seconds_to_time(current_time),
                    departure_time=self._seconds_to_time(current_time),
                    service_time=0
                )
            else:  # Customer
                customer = request.customers[node_index - 1]
                service_time = customer.service_time * 60
                stop = RouteStop(
                    type='customer',
                    id=customer.id,
                    name=customer.name,
                    coordinate=customer.coordinate,
                    demand=customer.demand,
                    load=route_load + customer.demand,
                    arrival_time=self._seconds_to_time(current_time),
                    departure_time=self._seconds_to_time(current_time + service_time),
                    service_time=customer.service_time,
                    wait_time=0
                )
                route_load += customer.demand
                current_time += service_time
            
            route.stops.append(stop)
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            
            # Distance and time calculation
            arc_distance = routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            route_distance += arc_distance
            
            # Time calculation
            if 'time_matrix' in data:
                travel_time = data['time_matrix'][node_index][manager.IndexToNode(index)]
                current_time += travel_time
                route_time += travel_time
        
        # Final depot stop
        route.stops.append(RouteStop(
            type='depot',
            id='DEPOT',
            name='Depo',
            coordinate=request.depot,
            load=route_load,
            arrival_time=self._seconds_to_time(current_time),
            departure_time=self._seconds_to_time(current_time),
            service_time=0
        ))
        
        # Route metrics
        route.total_distance = route_distance / 1000  # km
        route.total_cost = route_distance / 1000 * vehicle.cost_per_km
        route.total_load = route_load
        route.total_time = route_time / 3600  # hours
        route.utilization_rate = route_load / route.capacity if route.capacity > 0 else 0
        route.efficiency = route_load / route.total_distance if route.total_distance > 0 else 0
        
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
    
    def _time_to_seconds(self, time_str: str) -> int:
        """Convert HH:MM time string to seconds"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 3600 + minutes * 60
        except:
            return 0
    
    def _seconds_to_time(self, seconds: int) -> str:
        """Convert seconds to HH:MM time string"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
