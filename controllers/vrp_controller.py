"""
VRP Controller
"""
import time
import logging
from datetime import datetime
from typing import Dict, Any

from flask_restx import Resource, fields
from services.vrp_service import VRPService
from services.gemini_service import GeminiVRPService
from services.simple_vrp_service import SimpleVRPService
from services.validation_service import ValidationService
from models.vrp_models import VRPRequest, Customer, Vehicle, Coordinate, TimeWindow

logger = logging.getLogger(__name__)

class VRPController:
    def __init__(self, api):
        self.vrp_service = VRPService()
        self.gemini_service = GeminiVRPService()
        self.simple_service = SimpleVRPService()
        self.validation_service = ValidationService()
        self.api = api
        
        # Swagger models
        self._define_models()
        
        # Performance metrics
        self.solving_stats = {
            'total_requests': 0,
            'successful_solves': 0,
            'failed_solves': 0,
            'average_solving_time': 0.0,
            'total_solving_time': 0.0
        }
    
    def _define_models(self):
        """Define Swagger models"""
        self.coordinate_model = self.api.model('Coordinate', {
            'lat': fields.Float(required=True, description='Latitude'),
            'lng': fields.Float(required=True, description='Longitude')
        })
        
        self.time_window_model = self.api.model('TimeWindow', {
            'start': fields.String(required=True, description='Start time (HH:MM)'),
            'end': fields.String(required=True, description='End time (HH:MM)')
        })
        
        self.customer_model = self.api.model('Customer', {
            'id': fields.String(required=True, description='Customer ID'),
            'name': fields.String(required=True, description='Customer name'),
            'coordinate': fields.Nested(self.coordinate_model, required=True),
            'demand': fields.Integer(required=True, description='Demand amount'),
            'timeWindow': fields.Nested(self.time_window_model, description='Time window constraints'),
            'serviceTime': fields.Integer(description='Service time in minutes'),
            'priority': fields.Integer(description='Customer priority (1-10)'),
            'specialRequirements': fields.List(fields.String, description='Special requirements')
        })
        
        self.vehicle_model = self.api.model('Vehicle', {
            'id': fields.String(required=True, description='Vehicle ID'),
            'name': fields.String(required=True, description='Vehicle name'),
            'type': fields.String(required=True, description='Vehicle type'),
            'capacity': fields.Integer(required=True, description='Vehicle capacity'),
            'speed': fields.Float(description='Average speed km/h'),
            'costPerKm': fields.Float(description='Cost per kilometer'),
            'maxDistance': fields.Integer(description='Maximum distance per route'),
            'fuelType': fields.String(description='Fuel type'),
            'fuelConsumption': fields.Float(description='Fuel consumption L/100km'),
            'roadRestrictions': fields.List(fields.String, description='Road restrictions'),
            'isEcoFriendly': fields.Boolean(description='Eco-friendly vehicle'),
            'driverCost': fields.Float(description='Driver cost per hour'),
            'maintenanceCost': fields.Float(description='Maintenance cost per km')
        })
        
        self.vrp_request_model = self.api.model('VRPRequest', {
            'depot': fields.Nested(self.coordinate_model, required=True),
            'customers': fields.List(fields.Nested(self.customer_model), required=True),
            'vehicles': fields.List(fields.Nested(self.vehicle_model), required=True),
            'maxSolvingTime': fields.Integer(description='Maximum solving time in seconds'),
            'optimizationObjective': fields.String(description='Optimization objective: distance, cost, time, balanced'),
            'useTimeWindows': fields.Boolean(description='Enable time window constraints'),
            'useCapacityConstraints': fields.Boolean(description='Enable capacity constraints'),
            'useDistanceConstraints': fields.Boolean(description='Enable distance constraints'),
            'algorithm': fields.String(description='Algorithm: nearest_neighbor, genetic, ortools')
        })
    
    def solve_vrp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Solve VRP problem"""
        self.solving_stats['total_requests'] += 1
        start_time = time.time()
        
        try:
            # Convert request data to VRPRequest object
            vrp_request = self._convert_to_vrp_request(data)
            
            logger.info(f"VRP cozumu baslatiliyor...")
            logger.info(f"Depot: {vrp_request.depot}")
            logger.info(f"Musteriler: {len(vrp_request.customers)}")
            logger.info(f"Araclar: {len(vrp_request.vehicles)}")
            logger.info(f"Max solving time: {vrp_request.max_solving_time}s")
            logger.info(f"Time windows: {vrp_request.use_time_windows}")
            logger.info(f"Objective: {vrp_request.optimization_objective}")
            logger.info(f"Algorithm: {vrp_request.algorithm}")
            
            # Validate request
            validation_errors = self.validation_service.validate_vrp_request(vrp_request)
            if validation_errors:
                logger.warning(f"Validation errors: {validation_errors}")
                return {
                    'success': False,
                    'error': 'Input validation failed',
                    'details': validation_errors
                }
            
            # Solve VRP with fallback chain - Force multi-vehicle
            result = None
            
            # Always try Simple solver first for multi-vehicle guarantee
            logger.info("Using Simple solver for guaranteed multi-vehicle solution")
            result = self.simple_service.solve_vrp(vrp_request)
            
            if not result:
                logger.warning("Simple solver failed, trying Gemini")
                result = self.gemini_service.solve_vrp(vrp_request)
                if not result:
                    logger.warning("Gemini failed, trying OR-Tools as last resort")
                    result = self.vrp_service.solve_vrp(vrp_request)
            
            solving_time = time.time() - start_time
            
            if result:
                self.solving_stats['successful_solves'] += 1
                self.solving_stats['total_solving_time'] += solving_time
                self.solving_stats['average_solving_time'] = (
                    self.solving_stats['total_solving_time'] / self.solving_stats['successful_solves']
                )
                
                logger.info(f"VRP cozumu tamamlandi: {result.vehicles_used} arac, {result.customers_served} musteri")
                logger.info(f"Toplam mesafe: {result.total_distance} km")
                logger.info(f"Toplam maliyet: {result.total_cost} TL")
                logger.info(f"Cozum suresi: {result.solving_time} saniye")
                
                return {
                    'success': True,
                    'data': self._convert_solution_to_dict(result),
                    'metadata': {
                        'requestTime': datetime.now().isoformat(),
                        'solvingTime': solving_time,
                        'algorithm': vrp_request.algorithm,
                        'objective': vrp_request.optimization_objective,
                        'timeWindowsEnabled': vrp_request.use_time_windows
                    }
                }
            else:
                self.solving_stats['failed_solves'] += 1
                logger.warning("VRP cozumu bulunamadi")
                return {
                    'success': False,
                    'error': 'Çözüm bulunamadı',
                    'metadata': {
                        'requestTime': datetime.now().isoformat(),
                        'solvingTime': solving_time,
                        'algorithm': vrp_request.algorithm
                    }
                }
                
        except Exception as e:
            self.solving_stats['failed_solves'] += 1
            solving_time = time.time() - start_time
            logger.error(f"VRP cozum hatasi: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'requestTime': datetime.now().isoformat(),
                    'solvingTime': solving_time
                }
            }
    
    def _convert_to_vrp_request(self, data: Dict[str, Any]) -> VRPRequest:
        """Convert request data to VRPRequest object"""
        # Convert depot
        depot = Coordinate(
            lat=data['depot']['lat'],
            lng=data['depot']['lng']
        )
        
        # Convert customers
        customers = []
        for customer_data in data['customers']:
            coordinate = Coordinate(
                lat=customer_data['coordinate']['lat'],
                lng=customer_data['coordinate']['lng']
            )
            
            time_window = None
            if 'timeWindow' in customer_data and customer_data['timeWindow']:
                time_window = TimeWindow(
                    start=customer_data['timeWindow']['start'],
                    end=customer_data['timeWindow']['end']
                )
            
            customer = Customer(
                id=customer_data['id'],
                name=customer_data['name'],
                coordinate=coordinate,
                demand=customer_data['demand'],
                time_window=time_window,
                service_time=customer_data.get('serviceTime', 15),
                priority=customer_data.get('priority', 5),
                special_requirements=customer_data.get('specialRequirements', [])
            )
            customers.append(customer)
        
        # Convert vehicles
        vehicles = []
        for vehicle_data in data['vehicles']:
            vehicle = Vehicle(
                id=vehicle_data['id'],
                name=vehicle_data['name'],
                type=vehicle_data['type'],
                capacity=vehicle_data['capacity'],
                speed=vehicle_data.get('speed', 50.0),
                cost_per_km=vehicle_data.get('costPerKm', 2.5),
                max_distance=vehicle_data.get('maxDistance'),
                fuel_type=vehicle_data.get('fuelType'),
                fuel_consumption=vehicle_data.get('fuelConsumption'),
                road_restrictions=vehicle_data.get('roadRestrictions', []),
                is_eco_friendly=vehicle_data.get('isEcoFriendly', False),
                driver_cost=vehicle_data.get('driverCost'),
                maintenance_cost=vehicle_data.get('maintenanceCost')
            )
            vehicles.append(vehicle)
        
        return VRPRequest(
            depot=depot,
            customers=customers,
            vehicles=vehicles,
            max_solving_time=data.get('maxSolvingTime', 300),
            optimization_objective=data.get('optimizationObjective', 'balanced'),
            use_time_windows=data.get('useTimeWindows', False),
            use_capacity_constraints=data.get('useCapacityConstraints', True),
            use_distance_constraints=data.get('useDistanceConstraints', True),
            algorithm=data.get('algorithm', 'ortools')
        )
    
    def _convert_solution_to_dict(self, solution) -> Dict[str, Any]:
        """Convert VRPSolution object to dictionary"""
        routes = []
        for route in solution.routes:
            stops = []
            for stop in route.stops:
                stops.append({
                    'type': stop.type,
                    'id': stop.id,
                    'name': stop.name,
                    'coordinate': {
                        'lat': stop.coordinate.lat,
                        'lng': stop.coordinate.lng
                    },
                    'demand': stop.demand,
                    'load': stop.load,
                    'arrivalTime': stop.arrival_time,
                    'departureTime': stop.departure_time,
                    'serviceTime': stop.service_time,
                    'waitTime': stop.wait_time
                })
            
            routes.append({
                'vehicleId': route.vehicle_id,
                'vehicleName': route.vehicle_name,
                'vehicleType': route.vehicle_type,
                'capacity': route.capacity,
                'stops': stops,
                'totalDistance': route.total_distance,
                'totalCost': route.total_cost,
                'totalLoad': route.total_load,
                'totalTime': route.total_time,
                'utilizationRate': route.utilization_rate,
                'efficiency': route.efficiency
            })
        
        return {
            'routes': routes,
            'totalDistance': solution.total_distance,
            'totalCost': solution.total_cost,
            'totalTime': solution.total_time,
            'vehiclesUsed': solution.vehicles_used,
            'customersServed': solution.customers_served,
            'averageUtilization': solution.average_utilization,
            'averageEfficiency': solution.average_efficiency,
            'solvingTime': solution.solving_time,
            'status': solution.status,
            'algorithm': solution.algorithm,
            'timestamp': solution.timestamp
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get solving statistics"""
        return {
            'success': True,
            'stats': self.solving_stats,
            'timestamp': datetime.now().isoformat()
        }
