import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

class Database:
    """Database connection handler with lazy initialization"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        if self.connection is not None and not self.connection.closed:
            return  # Already connected
        
        try:
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                raise Exception("DATABASE_URL environment variable not set")
            
            # Railway uses postgres://, but psycopg2 needs postgresql://
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            print(f"🔄 Connecting to database...")
            self.connection = psycopg2.connect(
                database_url,
                cursor_factory=RealDictCursor,
                connect_timeout=10
            )
            print("✅ Database connected successfully!")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def execute(self, query, params=None, fetch=False):
        """Execute a database query"""
        # Lazy connection - connect when first query is executed
        if self.connection is None or self.connection.closed:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                cursor.close()
                return True
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"❌ Query execution failed: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()


class User:
    """User model"""
    
    @staticmethod
    def create_table(db):
        """Create users table"""
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        """
        db.execute(query)
        print("✅ Users table created!")
    
    @staticmethod
    def create(db, email, password):
        """Create a new user"""
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        query = """
        INSERT INTO users (email, password_hash)
        VALUES (%s, %s)
        RETURNING id, email, created_at;
        """
        result = db.execute(query, (email, password_hash), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def find_by_email(db, email):
        """Find user by email"""
        query = "SELECT * FROM users WHERE email = %s;"
        result = db.execute(query, (email,), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def find_by_id(db, user_id):
        """Find user by ID"""
        query = "SELECT id, email, created_at, last_login FROM users WHERE id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def get_by_id(db, user_id):
        """Get user by ID"""
        query = """
        SELECT id, email, created_at, last_login 
        FROM users 
        WHERE id = %s;
        """
        result = db.execute(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def update_last_login(db, user_id):
        """Update last login timestamp"""
        query = "UPDATE users SET last_login = %s WHERE id = %s;"
        db.execute(query, (datetime.now(), user_id))


class Behavior:
    """Behavior tracking model"""
    
    @staticmethod
    def create_table(db):
        """Create behaviors table"""
        query = """
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
        
        CREATE INDEX IF NOT EXISTS idx_behaviors_user_id ON behaviors(user_id);
        CREATE INDEX IF NOT EXISTS idx_behaviors_timestamp ON behaviors(timestamp);
        """
        db.execute(query)
    
    @staticmethod
    def create(db, user_id, data):
        """Create new behavior record"""
        query = """
        INSERT INTO behaviors (
            user_id, typing_speed, session_hour,
            location_lat, location_lng, device_model, device_os,
            screen_width, screen_height, session_duration
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, typing_speed, timestamp;
        """
        
        result = db.execute(query, (
            user_id,
            data.get('typing_speed', 0.0),
            data.get('session_hour', 0),
            data.get('location_lat', 0.0),
            data.get('location_lng', 0.0),
            data.get('device_model', 'Unknown'),
            data.get('device_os', 'Unknown'),
            data.get('screen_width', 0),
            data.get('screen_height', 0),
            data.get('session_duration', 0),
        ), fetch=True)
        
        return result[0] if result else None
    
    @staticmethod
    def get_user_behaviors(db, user_id, limit=100):
        """Get user's behavior history"""
        query = """
        SELECT id, user_id, typing_speed, session_hour,
               location_lat, location_lng, device_model, device_os,
               screen_width, screen_height, session_duration, 
               timestamp
        FROM behaviors
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT %s;
        """
        return db.execute(query, (user_id, limit), fetch=True) or []
    
    @staticmethod
    def count_user_behaviors(db, user_id):
        """Count total behaviors for user"""
        query = "SELECT COUNT(*) as count FROM behaviors WHERE user_id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0]['count'] if result else 0
    
    @staticmethod
    def get_recent_for_baseline(db, user_id, limit=50):
        """Get recent behaviors for baseline calculation"""
        query = """
        SELECT typing_speed, session_hour,
               location_lat, location_lng, device_model, device_os,
               screen_width, screen_height, session_duration
        FROM behaviors
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT %s;
        """
        return db.execute(query, (user_id, limit), fetch=True) or []

class BehaviorBaseline:
    """User behavior baseline model"""
    
    @staticmethod
    def create_table(db):
        """Create behavior_baselines table"""
        query = """
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
        """
        db.execute(query)
    
    @staticmethod
    def calculate_and_save(db, user_id):
        """Calculate and save baseline from recent behaviors"""
        behaviors = Behavior.get_recent_for_baseline(db, user_id, limit=50)
        
        if len(behaviors) < 5:
            return None
        
        # Calculate averages (SIMPLIFIED - no mouse/app_switches)
        avg_typing = sum(b['typing_speed'] for b in behaviors) / len(behaviors)
        avg_hour = sum(b['session_hour'] for b in behaviors) / len(behaviors)
        avg_lat = sum(b['location_lat'] for b in behaviors) / len(behaviors)
        avg_lng = sum(b['location_lng'] for b in behaviors) / len(behaviors)
        avg_screen_w = sum(b['screen_width'] for b in behaviors) / len(behaviors)
        avg_screen_h = sum(b['screen_height'] for b in behaviors) / len(behaviors)
        avg_duration = sum(b['session_duration'] for b in behaviors) / len(behaviors)
        
        # Most common device/os
        devices = [b['device_model'] for b in behaviors]
        oses = [b['device_os'] for b in behaviors]
        common_device = max(set(devices), key=devices.count)
        common_os = max(set(oses), key=oses.count)
        
        # Upsert baseline
        query = """
        INSERT INTO behavior_baselines (
            user_id, avg_typing_speed, avg_session_hour,
            avg_location_lat, avg_location_lng, common_device_model, common_device_os,
            avg_screen_width, avg_screen_height, avg_session_duration,
            total_sessions, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            avg_typing_speed = EXCLUDED.avg_typing_speed,
            avg_session_hour = EXCLUDED.avg_session_hour,
            avg_location_lat = EXCLUDED.avg_location_lat,
            avg_location_lng = EXCLUDED.avg_location_lng,
            common_device_model = EXCLUDED.common_device_model,
            common_device_os = EXCLUDED.common_device_os,
            avg_screen_width = EXCLUDED.avg_screen_width,
            avg_screen_height = EXCLUDED.avg_screen_height,
            avg_session_duration = EXCLUDED.avg_session_duration,
            total_sessions = EXCLUDED.total_sessions,
            updated_at = EXCLUDED.updated_at
        RETURNING *;
        """
        
        result = db.execute(query, (
            user_id, avg_typing, avg_hour,
            avg_lat, avg_lng, common_device, common_os,
            avg_screen_w, avg_screen_h, avg_duration,
            len(behaviors), datetime.now()
        ), fetch=True)
        
        return result[0] if result else None
    
    @staticmethod
    def get_by_user_id(db, user_id):
        """Get baseline for user"""
        query = "SELECT * FROM behavior_baselines WHERE user_id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0] if result else None
    
class RiskScore:
    """Risk score model"""
    
    @staticmethod
    def create_table(db):
        """Create risk scores table"""
        query = """
        CREATE TABLE IF NOT EXISTS risk_scores (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            risk_score FLOAT NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            action_taken VARCHAR(20) NOT NULL,
            typing_deviation FLOAT,
            location_deviation FLOAT,
            time_deviation FLOAT,
            device_deviation FLOAT,
            ml_anomaly_score FLOAT DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_risk_scores_user_id ON risk_scores(user_id);
        CREATE INDEX IF NOT EXISTS idx_risk_scores_timestamp ON risk_scores(timestamp);
        """
        db.execute(query)
        print("✅ Risk scores table created!")
    
    @staticmethod
    def create(db, user_id, risk_data):
        """Create a new risk score entry"""
        query = """
        INSERT INTO risk_scores (
            user_id, risk_score, risk_level, action_taken,
            typing_deviation, location_deviation, time_deviation, device_deviation,
            ml_anomaly_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, timestamp;
        """
        result = db.execute(query, (
            user_id,
            risk_data['risk_score'],
            risk_data['risk_level'],
            risk_data['action_taken'],
            risk_data.get('typing_deviation', 0),
            risk_data.get('location_deviation', 0),
            risk_data.get('time_deviation', 0),
            risk_data.get('device_deviation', 0),
            risk_data.get('ml_anomaly_score', 0)
        ), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def get_latest(db, user_id):
        """Get latest risk score for user"""
        query = """
        SELECT * FROM risk_scores 
        WHERE user_id = %s 
        ORDER BY timestamp DESC 
        LIMIT 1;
        """
        result = db.execute(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def get_history(db, user_id, limit=20):
        """Get risk score history"""
        query = """
        SELECT * FROM risk_scores 
        WHERE user_id = %s 
        ORDER BY timestamp DESC 
        LIMIT %s;
        """
        return db.execute(query, (user_id, limit), fetch=True)


class MLModel:
    """ML Model tracking"""
    
    @staticmethod
    def create_table(db):
        """Create ML models table"""
        query = """
        CREATE TABLE IF NOT EXISTS ml_models (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            is_trained BOOLEAN DEFAULT FALSE,
            training_samples INTEGER DEFAULT 0,
            features_count INTEGER DEFAULT 0,
            last_trained TIMESTAMP,
            model_version VARCHAR(50) DEFAULT '1.0'
        );
        """
        db.execute(query)
        print("✅ ML models table created!")
    
    @staticmethod
    def update_training_status(db, user_id, training_result):
        """Update ML model training status"""
        query = """
        INSERT INTO ml_models (user_id, is_trained, training_samples, features_count, last_trained)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            is_trained = EXCLUDED.is_trained,
            training_samples = EXCLUDED.training_samples,
            features_count = EXCLUDED.features_count,
            last_trained = EXCLUDED.last_trained
        RETURNING *;
        """
        result = db.execute(query, (
            user_id,
            True,
            training_result.get('training_samples', 0),
            training_result.get('features_used', 0),
            datetime.now()
        ), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def get_status(db, user_id):
        """Get ML model status for user"""
        query = "SELECT * FROM ml_models WHERE user_id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def is_trained(db, user_id):
        """Check if ML model is trained for user"""
        status = MLModel.get_status(db, user_id)
        return status['is_trained'] if status else False