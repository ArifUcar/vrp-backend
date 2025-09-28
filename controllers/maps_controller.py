"""
Maps Controller
"""
import logging
from typing import Dict, Any

from flask_restx import Resource, fields
from services.maps_service import MapsService
from models.vrp_models import Coordinate

logger = logging.getLogger(__name__)

class MapsController:
    def __init__(self, api, maps_service: MapsService):
        self.maps_service = maps_service
        self.api = api
        
        # Swagger models
        self._define_models()
    
    def _define_models(self):
        """Define Swagger models"""
        self.coordinate_model = self.api.model('Coordinate', {
            'lat': fields.Float(required=True, description='Latitude'),
            'lng': fields.Float(required=True, description='Longitude')
        })
        
        self.directions_request_model = self.api.model('DirectionsRequest', {
            'origin': fields.Nested(self.coordinate_model, required=True),
            'destination': fields.Nested(self.coordinate_model, required=True),
            'waypoints': fields.List(fields.Nested(self.coordinate_model)),
            'vehicleType': fields.String(description='Vehicle type for restrictions'),
            'avoid': fields.List(fields.String, description='Avoid options'),
            'restrictions': fields.List(fields.String, description='Restrictions')
        })
    
    def get_directions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get directions from Google Maps API"""
        try:
            # Convert coordinates
            origin = Coordinate(
                lat=data['origin']['lat'],
                lng=data['origin']['lng']
            )
            
            destination = Coordinate(
                lat=data['destination']['lat'],
                lng=data['destination']['lng']
            )
            
            waypoints = None
            if 'waypoints' in data and data['waypoints']:
                waypoints = [
                    Coordinate(lat=wp['lat'], lng=wp['lng'])
                    for wp in data['waypoints']
                ]
            
            # Get directions
            result = self.maps_service.get_directions(
                origin=origin,
                destination=destination,
                waypoints=waypoints,
                vehicle_type=data.get('vehicleType'),
                avoid=data.get('avoid', []),
                restrictions=data.get('restrictions', [])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Directions request error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
