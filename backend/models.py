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