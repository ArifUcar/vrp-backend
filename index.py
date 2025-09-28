"""
Netlify Function Entry Point
"""
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.vrp_controller import VRPController
from services.maps_service import MapsService
from flask_restx import Api
from flask import Flask

app = Flask(__name__)
api = Api(app)
vrp_controller = VRPController(api)
maps_service = MapsService()

def handler(event, context):
    """Netlify function handler"""
    try:
        # Parse request
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        body = event.get('body', '{}')
        
        # Handle CORS preflight
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': ''
            }
        
        # Route requests
        if path == '/api/vrp/solve' and method == 'POST':
            data = json.loads(body) if body else {}
            result = vrp_controller.solve_vrp(data)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        elif path == '/api/directions' and method == 'POST':
            data = json.loads(body) if body else {}
            result = maps_service.get_directions(data)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
