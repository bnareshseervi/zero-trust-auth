import psycopg
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

class Database:
    """Database connection handler"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg.connect(
                os.getenv('DATABASE_URL'),
                row_factory=dict_row
            )
            print("✅ Database connected successfully!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def execute(self, query, params=None, fetch=False):
        """Execute a database query"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
                    return True
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Query execution failed: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.connection:
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
    def verify_password(password_hash, password):
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def update_last_login(db, user_id):
        """Update last login timestamp"""
        query = "UPDATE users SET last_login = %s WHERE id = %s;"
        db.execute(query, (datetime.now(), user_id))


        # ADD TO models.py (after the User class)

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
            avg_tap_pressure FLOAT,
            tap_locations TEXT,
            location_lat FLOAT,
            location_lng FLOAT,
            device_model VARCHAR(100),
            device_os VARCHAR(50),
            screen_width INTEGER,
            screen_height INTEGER,
            session_hour INTEGER,
            session_duration INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_behaviors_user_id ON behaviors(user_id);
        CREATE INDEX IF NOT EXISTS idx_behaviors_timestamp ON behaviors(timestamp);
        """
        db.execute(query)
        print("✅ Behaviors table created!")
    
    @staticmethod
    def create(db, user_id, behavior_data):
        """Log new behavior data"""
        query = """
        INSERT INTO behaviors (
            user_id, typing_speed, avg_tap_pressure, tap_locations,
            location_lat, location_lng, device_model, device_os,
            screen_width, screen_height, session_hour, session_duration
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, timestamp;
        """
        result = db.execute(query, (
            user_id,
            behavior_data.get('typing_speed'),
            behavior_data.get('avg_tap_pressure'),
            behavior_data.get('tap_locations'),
            behavior_data.get('location_lat'),
            behavior_data.get('location_lng'),
            behavior_data.get('device_model'),
            behavior_data.get('device_os'),
            behavior_data.get('screen_width'),
            behavior_data.get('screen_height'),
            behavior_data.get('session_hour'),
            behavior_data.get('session_duration')
        ), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def get_user_behaviors(db, user_id, limit=50):
        """Get recent behaviors for a user"""
        query = """
        SELECT * FROM behaviors 
        WHERE user_id = %s 
        ORDER BY timestamp DESC 
        LIMIT %s;
        """
        return db.execute(query, (user_id, limit), fetch=True)
    
    @staticmethod
    def count_user_behaviors(db, user_id):
        """Count total behaviors for a user"""
        query = "SELECT COUNT(*) as count FROM behaviors WHERE user_id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0]['count'] if result else 0


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
            std_typing_speed FLOAT,
            avg_tap_pressure FLOAT,
            std_tap_pressure FLOAT,
            common_location_lat FLOAT,
            common_location_lng FLOAT,
            common_session_hour INTEGER,
            avg_session_duration FLOAT,
            total_sessions INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_baselines_user_id ON behavior_baselines(user_id);
        """
        db.execute(query)
        print("✅ Behavior Baselines table created!")
    
    @staticmethod
    def calculate_and_save(db, user_id):
        """Calculate baseline from user's behavior history"""
        # Get all behaviors for user
        behaviors = Behavior.get_user_behaviors(db, user_id, limit=100)
        
        if len(behaviors) < 5:
            return None  # Need at least 5 sessions
        
        # Calculate averages and standard deviations
        typing_speeds = [b['typing_speed'] for b in behaviors if b['typing_speed']]
        tap_pressures = [b['avg_tap_pressure'] for b in behaviors if b['avg_tap_pressure']]
        session_hours = [b['session_hour'] for b in behaviors if b['session_hour']]
        session_durations = [b['session_duration'] for b in behaviors if b['session_duration']]
        
        # Calculate stats
        import statistics
        
        baseline_data = {
            'avg_typing_speed': statistics.mean(typing_speeds) if typing_speeds else 0,
            'std_typing_speed': statistics.stdev(typing_speeds) if len(typing_speeds) > 1 else 0,
            'avg_tap_pressure': statistics.mean(tap_pressures) if tap_pressures else 0,
            'std_tap_pressure': statistics.stdev(tap_pressures) if len(tap_pressures) > 1 else 0,
            'common_session_hour': int(statistics.mode(session_hours)) if session_hours else 12,
            'avg_session_duration': statistics.mean(session_durations) if session_durations else 0,
            'total_sessions': len(behaviors)
        }
        
        # Get most common location
        locations = [(b['location_lat'], b['location_lng']) for b in behaviors 
                     if b['location_lat'] and b['location_lng']]
        if locations:
            baseline_data['common_location_lat'] = statistics.mean([loc[0] for loc in locations])
            baseline_data['common_location_lng'] = statistics.mean([loc[1] for loc in locations])
        else:
            baseline_data['common_location_lat'] = 0
            baseline_data['common_location_lng'] = 0
        
        # Save or update baseline
        query = """
        INSERT INTO behavior_baselines (
            user_id, avg_typing_speed, std_typing_speed, avg_tap_pressure,
            std_tap_pressure, common_location_lat, common_location_lng,
            common_session_hour, avg_session_duration, total_sessions, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) 
        DO UPDATE SET
            avg_typing_speed = EXCLUDED.avg_typing_speed,
            std_typing_speed = EXCLUDED.std_typing_speed,
            avg_tap_pressure = EXCLUDED.avg_tap_pressure,
            std_tap_pressure = EXCLUDED.std_tap_pressure,
            common_location_lat = EXCLUDED.common_location_lat,
            common_location_lng = EXCLUDED.common_location_lng,
            common_session_hour = EXCLUDED.common_session_hour,
            avg_session_duration = EXCLUDED.avg_session_duration,
            total_sessions = EXCLUDED.total_sessions,
            updated_at = CURRENT_TIMESTAMP
        RETURNING *;
        """
        result = db.execute(query, (
            user_id,
            baseline_data['avg_typing_speed'],
            baseline_data['std_typing_speed'],
            baseline_data['avg_tap_pressure'],
            baseline_data['std_tap_pressure'],
            baseline_data['common_location_lat'],
            baseline_data['common_location_lng'],
            baseline_data['common_session_hour'],
            baseline_data['avg_session_duration'],
            baseline_data['total_sessions']
        ), fetch=True)
        
        return result[0] if result else None
    
    @staticmethod
    def get_by_user_id(db, user_id):
        """Get baseline for a user"""
        query = "SELECT * FROM behavior_baselines WHERE user_id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0] if result else None


class RiskScore:
    """Risk score tracking model"""
    
    @staticmethod
    def create_table(db):
        """Create risk_scores table"""
        query = """
        CREATE TABLE IF NOT EXISTS risk_scores (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            risk_score FLOAT NOT NULL,
            typing_deviation FLOAT,
            location_deviation FLOAT,
            time_deviation FLOAT,
            device_deviation FLOAT,
            ml_anomaly_score FLOAT,
            risk_level VARCHAR(20),
            action_taken VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_risk_user_id ON risk_scores(user_id);
        CREATE INDEX IF NOT EXISTS idx_risk_timestamp ON risk_scores(timestamp);
        """
        db.execute(query)
        print("✅ Risk Scores table created!")
    
    @staticmethod
    def create(db, user_id, risk_data):
        """Log new risk score"""
        query = """
        INSERT INTO risk_scores (
            user_id, risk_score, typing_deviation, location_deviation,
            time_deviation, device_deviation, ml_anomaly_score,
            risk_level, action_taken
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, timestamp;
        """
        result = db.execute(query, (
            user_id,
            risk_data['risk_score'],
            risk_data.get('typing_deviation', 0),
            risk_data.get('location_deviation', 0),
            risk_data.get('time_deviation', 0),
            risk_data.get('device_deviation', 0),
            risk_data.get('ml_anomaly_score', 0),
            risk_data.get('risk_level', 'LOW'),
            risk_data.get('action_taken', 'ALLOW')
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
    
    # ADD to models.py

class MLModel:
    """ML Model training tracking"""
    
    @staticmethod
    def create_table(db):
        """Create ml_models table"""
        query = """
        CREATE TABLE IF NOT EXISTS ml_models (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            is_trained BOOLEAN DEFAULT FALSE,
            training_samples INTEGER,
            features_count INTEGER,
            last_trained TIMESTAMP,
            model_accuracy FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_ml_models_user_id ON ml_models(user_id);
        """
        db.execute(query)
        print("✅ ML Models table created!")
    
    @staticmethod
    def update_training_status(db, user_id, training_result):
        """Update ML model training status"""
        query = """
        INSERT INTO ml_models (
            user_id, is_trained, training_samples, features_count, last_trained
        ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) 
        DO UPDATE SET
            is_trained = EXCLUDED.is_trained,
            training_samples = EXCLUDED.training_samples,
            features_count = EXCLUDED.features_count,
            last_trained = CURRENT_TIMESTAMP
        RETURNING *;
        """
        result = db.execute(query, (
            user_id,
            training_result.get('success', False),
            training_result.get('training_samples', 0),
            training_result.get('features_used', 0)
        ), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def get_status(db, user_id):
        """Get ML model training status"""
        query = "SELECT * FROM ml_models WHERE user_id = %s;"
        result = db.execute(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    @staticmethod
    def is_trained(db, user_id):
        """Check if user has trained model"""
        status = MLModel.get_status(db, user_id)
        return status['is_trained'] if status else False