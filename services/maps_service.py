"""
Maps Service for Google Maps API integration
"""
import requests
import logging
from typing import Dict, List, Any, Optional
from models.vrp_models import Coordinate

logger = logging.getLogger(__name__)

class MapsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    def get_directions(self, 
                      origin: Coordinate, 
                      destination: Coordinate, 
                      waypoints: Optional[List[Coordinate]] = None,
                      vehicle_type: Optional[str] = None,
                      avoid: Optional[List[str]] = None,
                      restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get directions from Google Maps API"""
        try:
            # Build URL
            url = f"{self.base_url}/directions/json"
            
            # Parameters
            params = {
                'origin': f"{origin.lat},{origin.lng}",
                'destination': f"{destination.lat},{destination.lng}",
                'key': self.api_key
            }
            
            # Add waypoints
            if waypoints:
                waypoint_str = '|'.join([f"{wp.lat},{wp.lng}" for wp in waypoints])
                params['waypoints'] = waypoint_str
            
            # Add vehicle type
            if vehicle_type:
                params['vehicleType'] = vehicle_type
            
            # Add avoid options
            if avoid:
                params['avoid'] = '|'.join(avoid)
            
            # Add restrictions
            if restrictions:
                params['restrictions'] = '|'.join(restrictions)
            
            # Make request
            response = requests.get(url, params=params)
            result = response.json()
            
            if result['status'] == 'OK':
                logger.info("Directions API request successful")
                return {
                    'success': True,
                    'data': result
                }
            else:
                logger.warning(f"Directions API error: {result.get('error_message', 'Unknown error')}")
                return {
                    'success': False,
                    'error': result.get('error_message', 'Directions API error')
                }
                
        except Exception as e:
            logger.error(f"Directions API request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_vehicle_restrictions(self, vehicle_type: str) -> Dict[str, Any]:
        """Get vehicle-specific restrictions for Google Maps API"""
        restrictions = {
            'Tır': {
                'vehicleType': 'TRUCK',
                'avoid': ['tolls', 'highways'],
                'restrictions': ['maxWeight:40000', 'maxHeight:4.2', 'maxWidth:2.55']
            },
            'Kamyon': {
                'vehicleType': 'TRUCK',
                'avoid': ['tolls'],
                'restrictions': ['maxWeight:7500', 'maxHeight:4.0', 'maxWidth:2.5']
            },
            'Kamyonet': {
                'vehicleType': 'TRUCK',
                'avoid': [],
                'restrictions': ['maxWeight:3500', 'maxHeight:3.5', 'maxWidth:2.2']
            },
            'Minibüs': {
                'vehicleType': 'BUS',
                'avoid': ['tolls'],
                'restrictions': ['maxWeight:5000', 'maxHeight:3.8', 'maxWidth:2.5']
            },
            'Otobüs': {
                'vehicleType': 'BUS',
                'avoid': ['tolls', 'highways'],
                'restrictions': ['maxWeight:18000', 'maxHeight:4.0', 'maxWidth:2.55']
            },
            'Araba': {
                'vehicleType': 'CAR',
                'avoid': [],
                'restrictions': []
            }
        }
        
        return restrictions.get(vehicle_type, {
            'vehicleType': 'CAR',
            'avoid': [],
            'restrictions': []
        })
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """Geocode address to coordinates"""
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                'address': address,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result['status'] == 'OK':
                location = result['results'][0]['geometry']['location']
                return {
                    'success': True,
                    'coordinate': Coordinate(
                        lat=location['lat'],
                        lng=location['lng']
                    )
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error_message', 'Geocoding failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def reverse_geocode(self, coordinate: Coordinate) -> Dict[str, Any]:
        """Reverse geocode coordinates to address"""
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                'latlng': f"{coordinate.lat},{coordinate.lng}",
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result['status'] == 'OK':
                address = result['results'][0]['formatted_address']
                return {
                    'success': True,
                    'address': address
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error_message', 'Reverse geocoding failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
