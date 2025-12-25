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


# Keep all your User, Behavior, BehaviorBaseline, RiskScore, MLModel classes as they are...