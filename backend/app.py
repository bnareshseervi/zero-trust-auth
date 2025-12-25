from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import Config
from models import Database, User
import redis
import json

from models import Database, User, Behavior, BehaviorBaseline, RiskScore, MLModel

from models import Database, User, Behavior, BehaviorBaseline, RiskScore
from risk_calculator import RiskCalculator

from models import Database, User, Behavior, BehaviorBaseline, RiskScore, MLModel
from risk_calculator import RiskCalculator
from ml_engine import MLEngine

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
    try:
        db = get_db()  # Get DB on demand
        User.create_table(db)
        Behavior.create_table(db)
        BehaviorBaseline.create_table(db)
        RiskScore.create_table(db)
        MLModel.create_table(db)  # NEW!
        return jsonify({
            "success": True,
            "message": "All database tables created successfully!"
        }), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                "success": False,
                "error": "Email and password are required"
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Validate email format (basic)
        if '@' not in email or '.' not in email:
            return jsonify({
                "success": False,
                "error": "Invalid email format"
            }), 400
        
        # Validate password length
        if len(password) < 6:
            return jsonify({
                "success": False,
                "error": "Password must be at least 6 characters"
            }), 400
        
        # Check if user already exists
        existing_user = User.find_by_email(db, email)
        if existing_user:
            return jsonify({
                "success": False,
                "error": "User already exists with this email"
            }), 409
        
        # Create new user
        user = User.create(db, email, password)
        
        if user:
            return jsonify({
                "success": True,
                "message": "User registered successfully!",
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "created_at": str(user['created_at'])
                }
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create user"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                "success": False,
                "error": "Email and password are required"
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.find_by_email(db, email)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401
        
        # Verify password
        if not User.verify_password(user['password_hash'], password):
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401
        
        # Update last login
        User.update_last_login(db, user['id'])
        
        # Create JWT token
        access_token = create_access_token(identity=str(user['id']))
        
        # Store session in Redis (optional)
        if redis_client:
            redis_client.setex(
                f"session:{user['id']}", 
                86400,  # 24 hours
                json.dumps({"email": user['email']})
            )
        
        return jsonify({
            "success": True,
            "message": "Login successful!",
            "token": access_token,
            "user": {
                "id": user['id'],
                "email": user['email']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile (protected route)"""
    try:
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        
        # Fetch user from database
        user = User.find_by_id(db, current_user_id)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        return jsonify({
            "success": True,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "created_at": str(user['created_at']),
                "last_login": str(user['last_login']) if user.get('last_login') else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (clear Redis session)"""
    try:
        current_user_id = get_jwt_identity()
        
        # Remove session from Redis
        if redis_client:
            redis_client.delete(f"session:{current_user_id}")
        
        return jsonify({
            "success": True,
            "message": "Logout successful!"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# HEALTH CHECK ROUTES
# ============================================

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "success": True,
        "message": "Zero Trust Auth API is running!",
        "version": "1.0.0"
    }), 200


@app.route('/api/health', methods=['GET'])
def detailed_health():
    """Detailed health check"""
    health_status = {
        "database": False,
        "redis": False
    }
    
    # Check database
    try:
        get_db().execute()("SELECT 1;", fetch=True)
        health_status["database"] = True
    except:
        pass
    
    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            health_status["redis"] = True
    except:
        pass
    
    return jsonify({
        "success": True,
        "health": health_status
    }), 200

# ============================================
# BEHAVIOR TRACKING ROUTES
# ============================================

@app.route('/api/behavior/log', methods=['POST'])
@jwt_required()
def log_behavior():
    """Log user behavior data"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Behavior data is required"
            }), 400
        
        # Validate required fields
        required_fields = ['typing_speed', 'session_hour']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Log behavior
        behavior = Behavior.create(db, current_user_id, data)
        
        if not behavior:
            return jsonify({
                "success": False,
                "error": "Failed to log behavior"
            }), 500
        
        # Check if we have enough data to calculate baseline
        behavior_count = Behavior.count_user_behaviors(db, current_user_id)
        
        # Auto-calculate baseline after 5 behaviors
        baseline_updated = False
        if behavior_count >= 5:
            baseline = BehaviorBaseline.calculate_and_save(db, current_user_id)
            baseline_updated = baseline is not None
        
        return jsonify({
            "success": True,
            "message": "Behavior logged successfully",
            "behavior_id": behavior['id'],
            "total_behaviors": behavior_count,
            "baseline_updated": baseline_updated
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/behavior/history', methods=['GET'])
@jwt_required()
def get_behavior_history():
    """Get user's behavior history"""
    try:
        current_user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        behaviors = Behavior.get_user_behaviors(db, current_user_id, limit)
        
        # Convert to JSON-friendly format
        behavior_list = []
        for b in behaviors:
            behavior_list.append({
                'id': b['id'],
                'typing_speed': b['typing_speed'],
                'location': {
                    'lat': b['location_lat'],
                    'lng': b['location_lng']
                },
                'device': {
                    'model': b['device_model'],
                    'os': b['device_os']
                },
                'session_hour': b['session_hour'],
                'timestamp': str(b['timestamp'])
            })
        
        return jsonify({
            "success": True,
            "behaviors": behavior_list,
            "count": len(behavior_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/behavior/baseline', methods=['GET'])
@jwt_required()
def get_baseline():
    """Get user's behavior baseline"""
    try:
        current_user_id = get_jwt_identity()
        
        baseline = BehaviorBaseline.get_by_user_id(db, current_user_id)
        
        if not baseline:
            return jsonify({
                "success": False,
                "message": "No baseline calculated yet. Need at least 5 behavior logs.",
                "baseline": None
            }), 404
        
        return jsonify({
            "success": True,
            "baseline": {
                'avg_typing_speed': baseline['avg_typing_speed'],
                'std_typing_speed': baseline['std_typing_speed'],
                'common_location': {
                    'lat': baseline['common_location_lat'],
                    'lng': baseline['common_location_lng']
                },
                'common_session_hour': baseline['common_session_hour'],
                'total_sessions': baseline['total_sessions'],
                'updated_at': str(baseline['updated_at'])
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/behavior/baseline/recalculate', methods=['POST'])
@jwt_required()
def recalculate_baseline():
    """Manually trigger baseline recalculation"""
    try:
        current_user_id = get_jwt_identity()
        
        baseline = BehaviorBaseline.calculate_and_save(db, current_user_id)
        
        if not baseline:
            return jsonify({
                "success": False,
                "error": "Need at least 5 behavior logs to calculate baseline"
            }), 400
        
        return jsonify({
            "success": True,
            "message": "Baseline recalculated successfully",
            "baseline": {
                'avg_typing_speed': baseline['avg_typing_speed'],
                'total_sessions': baseline['total_sessions']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================
# RISK SCORING ROUTES
# ============================================

@app.route('/api/risk/calculate', methods=['POST'])
@jwt_required()
def calculate_risk():
    """Calculate risk score with ML enhancement"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Behavior data is required"
            }), 400
        
        # Get user's baseline
        baseline = BehaviorBaseline.get_by_user_id(db, current_user_id)
        
        if not baseline:
            # First log the behavior
            Behavior.create(db, current_user_id, data)
            
            return jsonify({
                "success": False,
                "message": "No baseline available yet. Behavior logged. Need at least 5 sessions.",
                "risk_score": 0,
                "risk_level": "UNKNOWN"
            }), 200
        
        # Get recent behaviors
        recent_behaviors = Behavior.get_user_behaviors(db, current_user_id, limit=20)
        
        # Check if ML model is trained
        ml_trained = MLModel.is_trained(db, current_user_id)
        
        if ml_trained:
            # Use ML-enhanced risk calculation
            ml_engine = MLEngine(current_user_id)
            ml_prediction = ml_engine.predict(data, recent_behaviors)
            
            if ml_prediction['success']:
                ml_score = ml_prediction['anomaly_score']
                
                # Calculate risk with ML
                risk_result = RiskCalculator.calculate_risk_with_ml(
                    data, baseline, recent_behaviors, ml_score
                )
            else:
                # Fallback to base calculation
                risk_result = RiskCalculator.calculate_risk(data, baseline, recent_behaviors)
                risk_result['ml_anomaly_score'] = 0
        else:
            # Use base risk calculation
            risk_result = RiskCalculator.calculate_risk(data, baseline, recent_behaviors)
            risk_result['ml_anomaly_score'] = 0
        
        # Log the risk score
        RiskScore.create(db, current_user_id, risk_result)
        
        # Log the behavior
        Behavior.create(db, current_user_id, data)
        
        # Check if we should auto-train/retrain
        behavior_count = Behavior.count_user_behaviors(db, current_user_id)
        
        # Auto-train after 10 behaviors if not trained
        if behavior_count == 10 and not ml_trained:
            ml_engine = MLEngine(current_user_id)
            training_result = ml_engine.train(recent_behaviors + [data])
            if training_result['success']:
                MLModel.update_training_status(db, current_user_id, training_result)
        
        # Auto-retrain every 20 behaviors
        elif ml_trained and behavior_count % 20 == 0:
            ml_engine = MLEngine(current_user_id)
            training_result = ml_engine.train(Behavior.get_user_behaviors(db, current_user_id, limit=100))
            if training_result['success']:
                MLModel.update_training_status(db, current_user_id, training_result)
        
        # Update baseline every 10 behaviors
        if behavior_count % 10 == 0:
            BehaviorBaseline.calculate_and_save(db, current_user_id)
        
        return jsonify({
            "success": True,
            "risk_score": risk_result['risk_score'],
            "risk_level": risk_result['risk_level'],
            "action": risk_result['action_taken'],
            "ml_enabled": ml_trained,
            "deviations": {
                'typing': risk_result['typing_deviation'],
                'location': risk_result['location_deviation'],
                'time': risk_result['time_deviation'],
                'device': risk_result['device_deviation'],
                'ml_anomaly': risk_result['ml_anomaly_score']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/risk/current', methods=['GET'])
@jwt_required()
def get_current_risk():
    """Get latest risk score for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        risk = RiskScore.get_latest(db, current_user_id)
        
        if not risk:
            return jsonify({
                "success": False,
                "message": "No risk scores calculated yet",
                "risk_score": 0
            }), 404
        
        return jsonify({
            "success": True,
            "risk": {
                'score': risk['risk_score'],
                'level': risk['risk_level'],
                'action': risk['action_taken'],
                'timestamp': str(risk['timestamp']),
                'deviations': {
                    'typing': risk['typing_deviation'],
                    'location': risk['location_deviation'],
                    'time': risk['time_deviation'],
                    'device': risk['device_deviation']
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/risk/history', methods=['GET'])
@jwt_required()
def get_risk_history():
    """Get risk score history"""
    try:
        current_user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        risks = RiskScore.get_history(db, current_user_id, limit)
        
        risk_list = []
        for r in risks:
            risk_list.append({
                'score': r['risk_score'],
                'level': r['risk_level'],
                'action': r['action_taken'],
                'timestamp': str(r['timestamp'])
            })
        
        return jsonify({
            "success": True,
            "risks": risk_list,
            "count": len(risk_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get complete dashboard data with ML status"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        user = User.find_by_id(db, current_user_id)
        
        # Get latest risk
        latest_risk = RiskScore.get_latest(db, current_user_id)
        
        # Get baseline
        baseline = BehaviorBaseline.get_by_user_id(db, current_user_id)
        
        # Get behavior count
        behavior_count = Behavior.count_user_behaviors(db, current_user_id)
        
        # Get recent risk history
        risk_history = RiskScore.get_history(db, current_user_id, limit=10)
        
        # Get ML status
        ml_status = MLModel.get_status(db, current_user_id)
        ml_trained = ml_status['is_trained'] if ml_status else False
        
        dashboard_data = {
            'user': {
                'email': user['email'],
                'member_since': str(user['created_at'])
            },
            'current_risk': {
                'score': latest_risk['risk_score'] if latest_risk else 0,
                'level': latest_risk['risk_level'] if latest_risk else 'UNKNOWN',
                'ml_score': latest_risk['ml_anomaly_score'] if latest_risk else 0,
                'last_updated': str(latest_risk['timestamp']) if latest_risk else None
            },
            'baseline_status': {
                'calculated': baseline is not None,
                'total_sessions': baseline['total_sessions'] if baseline else 0,
                'last_updated': str(baseline['updated_at']) if baseline else None
            },
            'ml_status': {
                'trained': ml_trained,
                'training_samples': ml_status['training_samples'] if ml_status else 0,
                'last_trained': str(ml_status['last_trained']) if ml_status and ml_status.get('last_trained') else None,
                'ready_to_train': behavior_count >= 10 and not ml_trained
            },
            'statistics': {
                'total_behaviors': behavior_count,
                'total_risk_checks': len(risk_history),
                'avg_risk_score': round(sum(r['risk_score'] for r in risk_history) / len(risk_history), 2) if risk_history else 0,
                'behaviors_until_ml': max(0, 10 - behavior_count) if not ml_trained else 0
            }
        }
        
        return jsonify({
            "success": True,
            "dashboard": dashboard_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
# ============================================
# MACHINE LEARNING ROUTES
# ============================================

@app.route('/api/ml/train', methods=['POST'])
@jwt_required()
def train_ml_model():
    """Train ML model for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's behavior history
        behaviors = Behavior.get_user_behaviors(db, current_user_id, limit=100)
        
        if len(behaviors) < 10:
            return jsonify({
                "success": False,
                "error": f"Need at least 10 behaviors to train. You have {len(behaviors)}.",
                "current_behaviors": len(behaviors)
            }), 400
        
        # Initialize ML engine
        ml_engine = MLEngine(current_user_id)
        
        # Train the model
        training_result = ml_engine.train(behaviors)
        
        if not training_result['success']:
            return jsonify(training_result), 400
        
        # Update database with training status
        MLModel.update_training_status(db, current_user_id, training_result)
        
        return jsonify({
            "success": True,
            "message": "ML model trained successfully!",
            "details": training_result
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/ml/status', methods=['GET'])
@jwt_required()
def get_ml_status():
    """Get ML model training status"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get status from database
        ml_status = MLModel.get_status(db, current_user_id)
        
        # Get model info
        ml_engine = MLEngine(current_user_id)
        model_info = ml_engine.get_model_info()
        
        # Get behavior count
        behavior_count = Behavior.count_user_behaviors(db, current_user_id)
        
        if not ml_status:
            return jsonify({
                "success": True,
                "trained": False,
                "message": "No model trained yet",
                "current_behaviors": behavior_count,
                "behaviors_needed": max(0, 10 - behavior_count)
            }), 200
        
        return jsonify({
            "success": True,
            "trained": ml_status['is_trained'],
            "training_samples": ml_status['training_samples'],
            "features_count": ml_status['features_count'],
            "last_trained": str(ml_status['last_trained']) if ml_status.get('last_trained') else None,
            "current_behaviors": behavior_count,
            "model_info": model_info
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/ml/predict', methods=['POST'])
@jwt_required()
def ml_predict():
    """Get ML prediction for behavior"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Behavior data is required"
            }), 400
        
        # Check if model is trained
        if not MLModel.is_trained(db, current_user_id):
            return jsonify({
                "success": False,
                "error": "ML model not trained yet. Train first with /api/ml/train"
            }), 400
        
        # Get recent behaviors for context
        recent_behaviors = Behavior.get_user_behaviors(db, current_user_id, limit=20)
        
        # Initialize ML engine and predict
        ml_engine = MLEngine(current_user_id)
        prediction = ml_engine.predict(data, recent_behaviors)
        
        if not prediction['success']:
            return jsonify(prediction), 400
        
        return jsonify({
            "success": True,
            "prediction": prediction
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/ml/retrain', methods=['POST'])
@jwt_required()
def retrain_ml_model():
    """Force retrain ML model"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get latest behaviors
        behaviors = Behavior.get_user_behaviors(db, current_user_id, limit=100)
        
        if len(behaviors) < 10:
            return jsonify({
                "success": False,
                "error": "Need at least 10 behaviors to retrain"
            }), 400
        
        # Train
        ml_engine = MLEngine(current_user_id)
        training_result = ml_engine.train(behaviors)
        
        if training_result['success']:
            MLModel.update_training_status(db, current_user_id, training_result)
        
        return jsonify({
            "success": training_result['success'],
            "message": "Model retrained successfully" if training_result['success'] else "Retraining failed",
            "details": training_result
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    print("\n" + "="*65)
    print("🚀 ZERO TRUST AUTH API - RAILWAY DEPLOYMENT")
    print("="*65 + "\n")
    
    # Railway provides PORT environment variable
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    print(f"🌐 Starting server on port {port}")
    print(f"🔧 Debug mode: {debug}\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)