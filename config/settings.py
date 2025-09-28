"""
Application Settings
"""
import os
from typing import Dict, Any

class Settings:
    """Application settings"""
    
    # API Configuration
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'AIzaSyCxQiL7wXty6805lLefMIw70Jhmy03C538')
    
    # VRP Configuration
    MAX_SOLVING_TIME = int(os.getenv('MAX_SOLVING_TIME', '300'))  # 5 minutes
    DEFAULT_COST_PER_KM = float(os.getenv('DEFAULT_COST_PER_KM', '2.5'))
    DEFAULT_SERVICE_TIME = int(os.getenv('DEFAULT_SERVICE_TIME', '15'))  # minutes
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'vrp_backend.log')
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'maxSolvingTime': cls.MAX_SOLVING_TIME,
            'defaultCostPerKm': cls.DEFAULT_COST_PER_KM,
            'defaultServiceTime': cls.DEFAULT_SERVICE_TIME,
            'host': cls.HOST,
            'port': cls.PORT,
            'debug': cls.DEBUG,
            'logLevel': cls.LOG_LEVEL,
            'logFile': cls.LOG_FILE,
            'corsOrigins': cls.CORS_ORIGINS,
            'googleMapsApiKey': '***' if cls.GOOGLE_MAPS_API_KEY else None
        }

