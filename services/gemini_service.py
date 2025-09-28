"""
Gemini AI VRP Solving Service
"""
import json
import logging
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from models.vrp_models import VRPRequest, VRPSolution, Route, RouteStop, Coordinate

logger = logging.getLogger(__name__)

class GeminiVRPService:
    def __init__(self):
        # Gemini API key
        self.api_key = "AIzaSyAUGgLSuERc11rZ7wxpJjDEecX3y0Me4OM"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def solve_vrp(self, request: VRPRequest) -> Optional[VRPSolution]:
        """Solve VRP using Gemini AI"""
        try:
            logger.info(f"Gemini VRP solving started for {len(request.customers)} customers, {len(request.vehicles)} vehicles")
            
            # Create prompt for Gemini
            prompt = self._create_vrp_prompt(request)
            logger.info(f"Gemini prompt created, length: {len(prompt)}")
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            logger.info(f"Gemini response received, length: {len(response.text)}")
            
            # Parse response
            solution = self._parse_gemini_response(response.text, request)
            
            if solution:
                logger.info(f"Gemini solution parsed successfully: {solution.vehicles_used} vehicles, {solution.customers_served} customers")
            else:
                logger.warning("Gemini solution parsing failed")
            
            return solution
            
        except Exception as e:
            logger.error(f"Gemini VRP solving error: {str(e)}")
            return None
    
    def _create_vrp_prompt(self, request: VRPRequest) -> str:
        """Create prompt for Gemini AI"""
        prompt = f"""
        Sen bir Vehicle Routing Problem (VRP) uzmanısın. Aşağıdaki VRP problemini çöz:

        DEPOT (Başlangıç noktası):
        - Koordinat: {request.depot.lat}, {request.depot.lng}

        MÜŞTERİLER:
        """
        
        for i, customer in enumerate(request.customers):
            prompt += f"""
        {i+1}. {customer.name}
           - Koordinat: {customer.coordinate.lat}, {customer.coordinate.lng}
           - Talep: {customer.demand}
           - Servis süresi: {customer.service_time} dakika
        """
        
        prompt += f"""
        ARAÇLAR:
        """
        
        for i, vehicle in enumerate(request.vehicles):
            prompt += f"""
        {i+1}. {vehicle.name} ({vehicle.type})
           - Kapasite: {vehicle.capacity}
           - Hız: {vehicle.speed} km/h
           - Maliyet: {vehicle.cost_per_km} TL/km
        """
        
        prompt += """
        GÖREV:
        1. Tüm müşterileri ziyaret et
        2. Her aracın kapasitesini aşma
        3. MUTLAKA TÜM ARAÇLARI KULLAN! (Tek araç kullanma - bu yasak!)
        4. Müşterileri araçlar arasında eşit dağıt
        5. Her aracın en az 1 müşterisi olsun
        6. Toplam mesafeyi minimize et
        7. Her aracın rotasını belirle
        
        ÖNEMLİ: Eğer 3 araç varsa, 3 aracı da kullan. Eğer 2 araç varsa, 2 aracı da kullan.
        Tek araç kullanmak kesinlikle yasak!

        ÇÖZÜM FORMATI (JSON) - ÖRNEK (3 ARAÇ, 3 MÜŞTERİ):
        {
            "routes": [
                {
                    "vehicle_id": "V001",
                    "vehicle_name": "Araç 1",
                    "stops": [
                        {
                            "type": "depot",
                            "name": "Depo",
                            "coordinate": {"lat": 41.009, "lng": 28.957}
                        },
                        {
                            "type": "customer",
                            "name": "Müşteri 1",
                            "coordinate": {"lat": 41.010, "lng": 28.958},
                            "demand": 50
                        },
                        {
                            "type": "depot",
                            "name": "Depo",
                            "coordinate": {"lat": 41.009, "lng": 28.957}
                        }
                    ],
                    "total_distance": 15.5,
                    "total_cost": 38.75,
                    "total_load": 50
                },
                {
                    "vehicle_id": "V002",
                    "vehicle_name": "Araç 2",
                    "stops": [
                        {
                            "type": "depot",
                            "name": "Depo",
                            "coordinate": {"lat": 41.009, "lng": 28.957}
                        },
                        {
                            "type": "customer",
                            "name": "Müşteri 2",
                            "coordinate": {"lat": 41.011, "lng": 28.959},
                            "demand": 50
                        },
                        {
                            "type": "depot",
                            "name": "Depo",
                            "coordinate": {"lat": 41.009, "lng": 28.957}
                        }
                    ],
                    "total_distance": 12.3,
                    "total_cost": 30.75,
                    "total_load": 50
                },
                {
                    "vehicle_id": "V003",
                    "vehicle_name": "Araç 3",
                    "stops": [
                        {
                            "type": "depot",
                            "name": "Depo",
                            "coordinate": {"lat": 41.009, "lng": 28.957}
                        },
                        {
                            "type": "customer",
                            "name": "Müşteri 3",
                            "coordinate": {"lat": 41.012, "lng": 28.960},
                            "demand": 50
                        },
                        {
                            "type": "depot",
                            "name": "Depo",
                            "coordinate": {"lat": 41.009, "lng": 28.957}
                        }
                    ],
                    "total_distance": 18.7,
                    "total_cost": 46.75,
                    "total_load": 50
                }
            ],
            "total_distance": 46.5,
            "total_cost": 116.25,
            "vehicles_used": 3,
            "customers_served": 3
        }

        Sadece JSON formatında cevap ver, başka açıklama yapma.
        """
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str, request: VRPRequest) -> Optional[VRPSolution]:
        """Parse Gemini response and create VRPSolution"""
        try:
            # Clean response text
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON
            solution_data = json.loads(response_text)
            
            # Create routes
            routes = []
            for route_data in solution_data.get('routes', []):
                route = self._create_route_from_data(route_data, request)
                if route:
                    routes.append(route)
            
            # Create solution
            solution = VRPSolution(
                routes=routes,
                total_distance=solution_data.get('total_distance', 0),
                total_cost=solution_data.get('total_cost', 0),
                total_time=0,  # Gemini'den gelmiyor
                vehicles_used=solution_data.get('vehicles_used', len(routes)),
                customers_served=solution_data.get('customers_served', 0),
                average_utilization=0,  # Hesaplanacak
                average_efficiency=0,   # Hesaplanacak
                solving_time=0,         # Gemini'den gelmiyor
                status='success',
                algorithm='Gemini AI',
                timestamp='2025-01-01T00:00:00'
            )
            
            return solution
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return None
    
    def _create_route_from_data(self, route_data: Dict, request: VRPRequest) -> Optional[Route]:
        """Create Route object from Gemini response data"""
        try:
            # Find vehicle info
            vehicle_id = route_data.get('vehicle_id', 'V001')
            vehicle_name = route_data.get('vehicle_name', 'Araç')
            
            # Find corresponding vehicle in request
            vehicle = None
            for v in request.vehicles:
                if v.name == vehicle_name or v.id == vehicle_id:
                    vehicle = v
                    break
            
            if not vehicle:
                vehicle = request.vehicles[0]  # Default to first vehicle
            
            # Create route
            route = Route(
                vehicle_id=vehicle_id,
                vehicle_name=vehicle_name,
                vehicle_type=vehicle.type,
                capacity=vehicle.capacity,
                stops=[],
                total_distance=route_data.get('total_distance', 0),
                total_cost=route_data.get('total_cost', 0),
                total_load=route_data.get('total_load', 0),
                total_time=0,
                utilization_rate=0,
                efficiency=0
            )
            
            # Create stops
            for stop_data in route_data.get('stops', []):
                stop = self._create_stop_from_data(stop_data, request)
                if stop:
                    route.stops.append(stop)
            
            # Calculate metrics
            if route.capacity > 0:
                route.utilization_rate = route.total_load / route.capacity
            if route.total_distance > 0:
                route.efficiency = route.total_load / route.total_distance
            
            return route
            
        except Exception as e:
            logger.error(f"Error creating route from data: {str(e)}")
            return None
    
    def _create_stop_from_data(self, stop_data: Dict, request: VRPRequest) -> Optional[RouteStop]:
        """Create RouteStop object from Gemini response data"""
        try:
            stop_type = stop_data.get('type', 'customer')
            
            if stop_type == 'depot':
                return RouteStop(
                    type='depot',
                    id='DEPOT',
                    name='Depo',
                    coordinate=request.depot,
                    load=0,
                    arrival_time='08:00',
                    departure_time='08:00',
                    service_time=0
                )
            else:
                # Find customer
                customer = None
                for c in request.customers:
                    if c.name == stop_data.get('name'):
                        customer = c
                        break
                
                if customer:
                    return RouteStop(
                        type='customer',
                        id=customer.id,
                        name=customer.name,
                        coordinate=customer.coordinate,
                        demand=customer.demand,
                        load=stop_data.get('demand', customer.demand),
                        arrival_time='09:00',  # Default time
                        departure_time='09:15',  # Default time
                        service_time=customer.service_time,
                        wait_time=0
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating stop from data: {str(e)}")
            return None
