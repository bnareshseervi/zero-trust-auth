import os
import json
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)

from config import Config
from models import (
    Database, User, Behavior,
    BehaviorBaseline, RiskScore, MLModel
)
from risk_calculator import RiskCalculator
from ml_engine import MLEngine

# =========================
# APP INITIALIZATION
# =========================

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
jwt = JWTManager(app)

# =========================
# DATABASE
# =========================

db = Database()

# =========================
# REDIS (OPTIONAL)
# =========================

redis_client = None
if getattr(Config, "REDIS_URL", None):
    try:
        redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠ Redis disabled: {e}")

# =========================
# HEALTH CHECKS (RAILWAY)
# =========================

@app.route("/", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "zero-trust-auth",
        "env": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }), 200

# =========================
# DATABASE SETUP (RUN ONCE)
# =========================

@app.route("/api/setup", methods=["POST"])
def setup():
    try:
        User.create_table(db)
        Behavior.create_table(db)
        BehaviorBaseline.create_table(db)
        RiskScore.create_table(db)
        MLModel.create_table(db)

        return jsonify({
            "success": True,
            "message": "Database tables created"
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# AUTH ROUTES
# =========================

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email & password required"}), 400

    if User.find_by_email(db, email):
        return jsonify({"success": False, "error": "User exists"}), 409

    user = User.create(db, email, password)

    return jsonify({
        "success": True,
        "user": {"id": user["id"], "email": user["email"]}
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    user = User.find_by_email(db, email)
    if not user or not User.verify_password(user["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user["id"]))

    if redis_client:
        redis_client.setex(f"session:{user['id']}", 86400, json.dumps({"email": email}))

    return jsonify({
        "success": True,
        "token": token
    }), 200

# =========================
# ERROR HANDLERS
# =========================

@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(_):
    return jsonify({"success": False, "error": "Server error"}), 500

# =========================
# LOCAL RUN (RAILWAY IGNORES)
# =========================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
