"""
Advanced VRP Solver Backend - Modular Structure
"""
from flask import Flask
from flask_cors import CORS
from flask_restx import Api, Resource
import logging
from datetime import datetime

from config.settings import Settings
from controllers.vrp_controller import VRPController
from controllers.maps_controller import MapsController
from services.maps_service import MapsService

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['*'])  # Netlify için tüm origin'lere izin ver

# Logging configuration
logging.basicConfig(
    level=getattr(logging, Settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Swagger API setup
api = Api(
    app,
    version='2.0',
    title='Advanced VRP Solver API',
    description='Advanced Vehicle Routing Problem Solver with OR-Tools, Time Windows, and Multi-Objective Optimization',
    doc='/swagger/',
    prefix='/api',
    contact='VRP Team',
    contact_email='support@vrp-solver.com'
)

# Initialize services
maps_service = MapsService(Settings.GOOGLE_MAPS_API_KEY)

# Initialize controllers
vrp_controller = VRPController(api)
maps_controller = MapsController(api, maps_service)

# API Routes
@api.route('/vrp/solve')
class VRPSolver(Resource):
    @api.expect(vrp_controller.vrp_request_model)
    @api.doc('solve_vrp', description='Solve Vehicle Routing Problem using advanced OR-Tools with time windows and multi-objective optimization')
    def post(self):
        """VRP çözümü endpoint'i - Gelişmiş OR-Tools ile optimize edilmiş çözüm"""
        return vrp_controller.solve_vrp(api.payload)

@api.route('/directions')
class Directions(Resource):
    @api.expect(maps_controller.directions_request_model)
    @api.doc('get_directions', description='Get directions from Google Maps API with vehicle restrictions')
    def post(self):
        """Google Maps Directions API proxy - Araç tipine göre kısıtlamalar ile"""
        return maps_controller.get_directions(api.payload)

if __name__ == '__main__':
    print("🚀 Advanced VRP Backend v2.0 (Modular) başlatılıyor...")
    print("📚 OR-Tools entegrasyonu aktif")
    print("🕐 Zaman penceresi desteği")
    print("🎯 Çoklu hedef optimizasyonu")
    print("📊 Performans metrikleri")
    print("🏗️ Modüler mimari")
    print("📖 Swagger UI: http://localhost:5000/swagger/")
    print("🔍 Health Check: http://localhost:5000/api/health")
    print("📈 Statistics: http://localhost:5000/api/stats")
    print("⚙️ Configuration: http://localhost:5000/api/config")
    
    logger.info("Advanced VRP Backend (Modular) starting...")
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
