from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import Config
from models import Database, User, Behavior, BehaviorBaseline, RiskScore, MLModel
from risk_calculator import RiskCalculator
from ml_engine import MLEngine
import redis
import json
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Initialize Database 
db = Database()

# Initialize Redis
try:
    redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("✅ Redis connected successfully!")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    redis_client = None


# ============================================
# DATABASE SETUP ROUTE (Run once)
# ============================================

@app.route('/api/setup', methods=['POST'])
def setup_database():
    """Initialize database tables (run once)"""
    try:
        User.create_table(db)
        Behavior.create_table(db)
        BehaviorBaseline.create_table(db)
        RiskScore.create_table(db)
        MLModel.create_table(db)
        return jsonify({
            "success": True,
            "message": "All database tables created successfully!"
        }), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route("/api/health", methods=["GET"])
def health_check():
     return jsonify({
        "status": "ok",
        "service": "zero-trust-auth",
        "env": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }), 200
