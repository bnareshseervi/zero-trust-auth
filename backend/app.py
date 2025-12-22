from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import Config
from models import Database, User
import redis
import json

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
        return jsonify({
            "success": True,
            "message": "Database tables created successfully!"
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
        db.execute("SELECT 1;", fetch=True)
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
    print("\n" + "="*50)
    print("🚀 ZERO TRUST AUTH API STARTING...")
    print("="*50)
    print("\n📋 Available Endpoints:")
    print("  POST   /api/setup              - Setup database")
    print("  POST   /api/auth/register      - Register user")
    print("  POST   /api/auth/login         - Login user")
    print("  GET    /api/auth/profile       - Get profile (requires token)")
    print("  POST   /api/auth/logout        - Logout user")
    print("  GET    /api/health             - Health check")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)