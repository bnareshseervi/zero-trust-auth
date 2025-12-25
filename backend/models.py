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
        password_hash = generate_password_hash(password)
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
       query = "SELECT id, email FROM users WHERE id = %s;"
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
    """Behavior logging model"""
    
    @staticmethod
    def create_table(db):
        """Create behavior table"""
        query = """
        CREATE TABLE IF NOT EXISTS behaviors (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            typing_speed FLOAT,
            avg_tap_pressure FLOAT,
            location_lat FLOAT,
            location_lng FLOAT,
            device_model VARCHAR(100),
            device_os VARCHAR(50),
            session_hour INTEGER,
            session_duration INTEGER,
            screen_width INTEGER,
            screen_height INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_behaviors_user_id ON behaviors(user_id);
        CREATE INDEX IF NOT EXISTS idx_behaviors_timestamp ON behaviors(timestamp);
        """
        db.execute(query)
        print("✅ Behaviors table created!")
    
    @staticmethod
    def create(db, user_id, behavior_data):
        """Log a new behavior"""
        query = """
        INSERT INTO behaviors (
            user_id, typing_speed, avg_tap_pressure, location_lat, location_lng,
            device_model, device_os, session_hour, session_duration,
            screen_width, screen_height
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, timestamp;
        """
        result = db.execute(query, (
            user_id,
            behavior_data.get('typing_speed', 0),
            behavior_data.get('avg_tap_pressure', 0),
            behavior_data.get('location_lat', 0),
            behavior_data.get('location_lng', 0),
            behavior_data.get('device_model', ''),
            behavior_data.get('device_os', ''),
            behavior_data.get('session_hour', datetime.now().hour),
            behavior_data.get('session_duration', 0),
            behavior_data.get('screen_width', 1080),
            behavior_data.get('screen_height', 2400)
        ), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def get_user_behaviors(db, user_id, limit=100):
        """Get user's behavior history"""
        query = """
        SELECT * FROM behaviors 
        WHERE user_id = %s 
        ORDER BY timestamp DESC 
        LIMIT %s;
        """
        return db.execute(query, (user_id, limit), fetch=True)
    
    @staticmethod
    def count_user_behaviors(db, user_id):
        """Count total behaviors for user"""
        query = "SELECT COUNT(*) as count FROM behaviors WHERE user_id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0]['count'] if result else 0


class BehaviorBaseline:
    """Behavior baseline model"""
    
    @staticmethod
    def create_table(db):
        """Create baseline table"""
        query = """
        CREATE TABLE IF NOT EXISTS behavior_baselines (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            avg_typing_speed FLOAT,
            std_typing_speed FLOAT,
            common_location_lat FLOAT,
            common_location_lng FLOAT,
            common_session_hour INTEGER,
            total_sessions INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        db.execute(query)
        print("✅ Behavior baselines table created!")
    
    @staticmethod
    def calculate_and_save(db, user_id):
        """Calculate and save baseline from user's behaviors"""
        behaviors = Behavior.get_user_behaviors(db, user_id, limit=100)
        
        if len(behaviors) < 5:
            return None
        
        # Calculate statistics
        typing_speeds = [b['typing_speed'] for b in behaviors if b['typing_speed']]
        avg_typing = sum(typing_speeds) / len(typing_speeds) if typing_speeds else 0
        
        # Calculate standard deviation
        if len(typing_speeds) > 1:
            variance = sum((x - avg_typing) ** 2 for x in typing_speeds) / len(typing_speeds)
            std_typing = variance ** 0.5
        else:
            std_typing = 0
        
        # Most common location (average)
        lats = [b['location_lat'] for b in behaviors if b['location_lat']]
        lngs = [b['location_lng'] for b in behaviors if b['location_lng']]
        common_lat = sum(lats) / len(lats) if lats else 0
        common_lng = sum(lngs) / len(lngs) if lngs else 0
        
        # Most common hour
        hours = [b['session_hour'] for b in behaviors if b['session_hour'] is not None]
        common_hour = max(set(hours), key=hours.count) if hours else 12
        
        # Save or update
        query = """
        INSERT INTO behavior_baselines (
            user_id, avg_typing_speed, std_typing_speed, 
            common_location_lat, common_location_lng, 
            common_session_hour, total_sessions, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            avg_typing_speed = EXCLUDED.avg_typing_speed,
            std_typing_speed = EXCLUDED.std_typing_speed,
            common_location_lat = EXCLUDED.common_location_lat,
            common_location_lng = EXCLUDED.common_location_lng,
            common_session_hour = EXCLUDED.common_session_hour,
            total_sessions = EXCLUDED.total_sessions,
            updated_at = EXCLUDED.updated_at
        RETURNING *;
        """
        result = db.execute(query, (
            user_id, avg_typing, std_typing, 
            common_lat, common_lng, 
            common_hour, len(behaviors), datetime.now()
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