import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from config import Config
from models import Database, User, Behavior, BehaviorBaseline, RiskScore, MLModel
from risk_calculator import RiskCalculator

# Initialize Flask
app = Flask(__name__)
app.config.from_object(Config)

# CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# JWT
jwt = JWTManager(app)

# Database - lazy initialization
db = Database()

# ==========================================
# AUTO-INITIALIZE DATABASE ON STARTUP
# ==========================================
def initialize_database():
    """Auto-create all database tables if they don't exist"""
    
    def initialize_database():     
        try:
            # Create users table
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );
            """)
            
            # Create behaviors table (SIMPLIFIED - no mouse_speed/app_switches)
            db.execute("""
                CREATE TABLE IF NOT EXISTS behaviors (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    typing_speed FLOAT,
                    session_hour INTEGER,
                    location_lat FLOAT,
                    location_lng FLOAT,
                    device_model VARCHAR(255),
                    device_os VARCHAR(255),
                    screen_width INTEGER,
                    screen_height INTEGER,
                    session_duration INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create behavior_baselines table (SIMPLIFIED)
            db.execute("""
                CREATE TABLE IF NOT EXISTS behavior_baselines (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    avg_typing_speed FLOAT,
                    avg_session_hour FLOAT,
                    avg_location_lat FLOAT,
                    avg_location_lng FLOAT,
                    common_device_model VARCHAR(255),
                    common_device_os VARCHAR(255),
                    avg_screen_width FLOAT,
                    avg_screen_height FLOAT,
                    avg_session_duration FLOAT,
                    total_sessions INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create risk_scores table
            db.execute("""
                CREATE TABLE IF NOT EXISTS risk_scores (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    risk_score FLOAT NOT NULL,
                    risk_level VARCHAR(50),
                    action_taken VARCHAR(100),
                    typing_deviation FLOAT,
                    location_deviation FLOAT,
                    time_deviation FLOAT,
                    device_deviation FLOAT,
                    ml_anomaly_score FLOAT DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create ml_models table
            db.execute("""
                CREATE TABLE IF NOT EXISTS ml_models (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    is_trained BOOLEAN DEFAULT FALSE,
                    training_samples INTEGER DEFAULT 0,
                    features_count INTEGER DEFAULT 0,
                    last_trained TIMESTAMP
                );
            """)
            
            # Create indexes
            db.execute("CREATE INDEX IF NOT EXISTS idx_behaviors_user_id ON behaviors(user_id);")
            db.execute("CREATE INDEX IF NOT EXISTS idx_behaviors_timestamp ON behaviors(timestamp);")
            db.execute("CREATE INDEX IF NOT EXISTS idx_risk_scores_user_id ON risk_scores(user_id);")
            db.execute("CREATE INDEX IF NOT EXISTS idx_risk_scores_timestamp ON risk_scores(timestamp);")
            
            print("✅ Database tables created successfully!")
            
        except Exception as init_error:
            print(f"❌ Database initialization failed: {init_error}")
            raise

# Run initialization
initialize_database()

# Redis (optional)
redis_client = None
try:
    import redis
    if Config.REDIS_URL:
        redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connected")
except Exception as e:
    print(f"⚠️ Redis unavailable: {e}")

# ==========================================
# HEALTH & SETUP
# ==========================================

@app.route('/', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "zero-trust-auth"
    }), 200

@app.route('/api/setup', methods=['POST'])
def setup():
    try:
        User.create_table(db)
        Behavior.create_table(db)
        BehaviorBaseline.create_table(db)
        RiskScore.create_table(db)
        MLModel.create_table(db)
        return jsonify({"success": True, "message": "Database initialized"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# AUTHENTICATION
# ==========================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be 6+ characters"}), 400
        
        if User.find_by_email(db, email):
            return jsonify({"success": False, "error": "User already exists"}), 409
        
        user = User.create(db, email, password)
        
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "user": {"id": user['id'], "email": user['email']}
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        user = User.find_by_email(db, email)
        
        if not user:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401
        
        if not User.verify_password(user['password_hash'], password):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401
        
        token = create_access_token(identity=str(user['id']))
        
        if redis_client:
            try:
                redis_client.setex(f"session:{user['id']}", 86400, json.dumps({"email": email}))
            except:
                pass
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {"id": user['id'], "email": user['email']}
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(db, user_id)
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "created_at": str(user.get('created_at', '')),
                "last_login": str(user.get('last_login', ''))
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        if redis_client:
            try:
                redis_client.delete(f"session:{user_id}")
            except:
                pass
        return jsonify({"success": True, "message": "Logged out"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# BEHAVIOR TRACKING
# ==========================================

@app.route('/api/behavior/log', methods=['POST'])
@jwt_required()
def log_behavior():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        behavior = Behavior.create(db, user_id, data)
        behavior_count = Behavior.count_user_behaviors(db, user_id)
        
        baseline_updated = False
        if behavior_count >= 5:
            baseline = BehaviorBaseline.calculate_and_save(db, user_id)
            baseline_updated = baseline is not None
        
        return jsonify({
            "success": True,
            "message": "Behavior logged",
            "behavior_id": behavior['id'],
            "total_behaviors": behavior_count,
            "baseline_updated": baseline_updated
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/behavior/baseline', methods=['GET'])
@jwt_required()
def get_baseline():
    try:
        user_id = get_jwt_identity()
        baseline = BehaviorBaseline.get_by_user_id(db, user_id)
        
        if not baseline:
            return jsonify({
                "success": False,
                "message": "No baseline yet. Need 5+ behaviors."
            }), 404
        
        return jsonify({
            "success": True,
            "baseline": {
                "avg_typing_speed": baseline['avg_typing_speed'],
                "total_sessions": baseline['total_sessions']
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# RISK CALCULATION
# ==========================================

@app.route('/api/risk/calculate', methods=['POST'])
@jwt_required()
def calculate_risk():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get baseline
        baseline = BehaviorBaseline.get_by_user_id(db, user_id)
        
        if not baseline:
            # Log behavior anyway
            Behavior.create(db, user_id, data)
            return jsonify({
                "success": False,
                "message": "No baseline yet. Behavior logged. Need 5+ sessions.",
                "risk_score": 0,
                "risk_level": "UNKNOWN"
            }), 200
        
        # Get recent behaviors
        recent = Behavior.get_user_behaviors(db, user_id, limit=20)
        
        # Calculate risk
        risk_result = RiskCalculator.calculate_risk(data, baseline, recent)
        
        # Log risk
        RiskScore.create(db, user_id, risk_result)
        
        # Log behavior
        Behavior.create(db, user_id, data)
        
        # Update baseline every 10 behaviors
        count = Behavior.count_user_behaviors(db, user_id)
        if count % 10 == 0:
            BehaviorBaseline.calculate_and_save(db, user_id)
        
        return jsonify({
            "success": True,
            "risk_score": risk_result['risk_score'],
            "risk_level": risk_result['risk_level'],
            "action": risk_result['action_taken'],
            "deviations": {
                "typing": risk_result['typing_deviation'],
                "location": risk_result['location_deviation'],
                "time": risk_result['time_deviation'],
                "device": risk_result['device_deviation']
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/risk/current', methods=['GET'])
@jwt_required()
def get_current_risk():
    try:
        user_id = get_jwt_identity()
        risk = RiskScore.get_latest(db, user_id)
        
        if not risk:
            return jsonify({
                "success": False,
                "message": "No risk scores yet"
            }), 404
        
        return jsonify({
            "success": True,
            "risk": {
                "score": risk['risk_score'],
                "level": risk['risk_level'],
                "action": risk['action_taken'],
                "timestamp": str(risk['timestamp'])
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/risk/history', methods=['GET'])
@jwt_required()
def get_risk_history():
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        risks = RiskScore.get_history(db, user_id, limit)
        
        risk_list = [{
            "score": r['risk_score'],
            "level": r['risk_level'],
            "action": r['action_taken'],
            "timestamp": str(r['timestamp'])
        } for r in risks]
        
        return jsonify({
            "success": True,
            "risks": risk_list,
            "count": len(risk_list)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# DASHBOARD
# ==========================================

@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        
        user = User.get_by_id(db, user_id)
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        latest_risk = RiskScore.get_latest(db, user_id)
        baseline = BehaviorBaseline.get_by_user_id(db, user_id)
        behavior_count = Behavior.count_user_behaviors(db, user_id)
        risk_history = RiskScore.get_history(db, user_id, limit=10)
        ml_status = MLModel.get_status(db, user_id)
        
        return jsonify({
            "success": True,
            "dashboard": {
                "user": {
                    "email": user['email'],
                    "member_since": str(user.get('created_at', ''))
                },
                "current_risk": {
                    "score": latest_risk['risk_score'] if latest_risk else 0,
                    "level": latest_risk['risk_level'] if latest_risk else "UNKNOWN",
                    "ml_score": latest_risk.get('ml_anomaly_score', 0) if latest_risk else 0,
                    "last_updated": str(latest_risk['timestamp']) if latest_risk else None
                },
                "baseline_status": {
                    "calculated": baseline is not None,
                    "total_sessions": baseline['total_sessions'] if baseline else 0,
                    "last_updated": str(baseline.get('updated_at')) if baseline else None
                },
                "ml_status": {
                    "trained": ml_status['is_trained'] if ml_status else False,
                    "training_samples": ml_status.get('training_samples', 0) if ml_status else 0,
                    "last_trained": str(ml_status.get('last_trained')) if ml_status and ml_status.get('last_trained') else None,
                    "ready_to_train": behavior_count >= 10 and (not ml_status or not ml_status['is_trained'])
                },
                "statistics": {
                    "total_behaviors": behavior_count,
                    "total_risk_checks": len(risk_history),
                    "avg_risk_score": sum(r['risk_score'] for r in risk_history) / len(risk_history) if risk_history else 0,
                    "behaviors_until_ml": max(0, 10 - behavior_count) if not ml_status or not ml_status.get('is_trained') else 0
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# ML ENDPOINTS
# ==========================================

@app.route('/api/ml/train', methods=['POST'])
@jwt_required()
def train_model():
    try:
        user_id = get_jwt_identity()
        behaviors = Behavior.get_user_behaviors(db, user_id, limit=100)
        
        if len(behaviors) < 10:
            return jsonify({
                "success": False,
                "error": f"Need 10+ behaviors. You have {len(behaviors)}"
            }), 400
        
        # Simulate training (would use ml_engine.py in full version)
        MLModel.update_training_status(db, user_id, {
            "success": True,
            "training_samples": len(behaviors),
            "features_used": 18
        })
        
        return jsonify({
            "success": True,
            "message": "Model trained successfully",
            "training_samples": len(behaviors)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ml/status', methods=['GET'])
@jwt_required()
def get_ml_status():
    try:
        user_id = get_jwt_identity()
        ml_status = MLModel.get_status(db, user_id)
        behavior_count = Behavior.count_user_behaviors(db, user_id)
        
        if not ml_status:
            return jsonify({
                "success": True,
                "trained": False,
                "current_behaviors": behavior_count,
                "behaviors_needed": max(0, 10 - behavior_count)
            }), 200
        
        return jsonify({
            "success": True,
            "trained": ml_status['is_trained'],
            "training_samples": ml_status.get('training_samples', 0),
            "current_behaviors": behavior_count
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# ==========================================
# RUN
# ==========================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    print("\n" + "="*60)
    print("🚀 ZERO TRUST AUTH API")
    print("="*60)
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("="*60 + "\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)