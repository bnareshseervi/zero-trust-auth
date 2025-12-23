import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

class MLEngine:
    """Machine Learning Engine for Behavioral Anomaly Detection"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.model = None
        self.scaler = None
        self.feature_names = [
            'typing_speed',
            'avg_tap_pressure',
            'location_lat',
            'location_lng',
            'session_hour',
            'session_duration',
            'screen_width',
            'screen_height'
        ]
        self.model_path = f'ml_models/user_{user_id}_model.joblib'
        self.scaler_path = f'ml_models/user_{user_id}_scaler.joblib'
    
    def extract_features(self, behaviors):
        """
        Extract feature vectors from behavior data
        
        Args:
            behaviors: List of behavior dictionaries
        
        Returns:
            numpy array of features
        """
        features = []
        
        for behavior in behaviors:
            feature_vector = [
                behavior.get('typing_speed', 0),
                behavior.get('avg_tap_pressure', 0),
                behavior.get('location_lat', 0),
                behavior.get('location_lng', 0),
                behavior.get('session_hour', 12),
                behavior.get('session_duration', 0),
                behavior.get('screen_width', 1080),
                behavior.get('screen_height', 2400)
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def engineer_features(self, behaviors):
        """
        Create additional engineered features
        
        Args:
            behaviors: List of behavior dictionaries
        
        Returns:
            pandas DataFrame with original + engineered features
        """
        df = pd.DataFrame(behaviors)
        
        # Original features
        feature_df = pd.DataFrame()
        for feature in self.feature_names:
            feature_df[feature] = df.get(feature, 0)
        
        # Engineered features
        
        # 1. Time-based features
        feature_df['is_night'] = (feature_df['session_hour'] >= 22) | (feature_df['session_hour'] <= 6)
        feature_df['is_morning'] = (feature_df['session_hour'] >= 6) & (feature_df['session_hour'] <= 12)
        feature_df['is_afternoon'] = (feature_df['session_hour'] >= 12) & (feature_df['session_hour'] <= 18)
        feature_df['is_evening'] = (feature_df['session_hour'] >= 18) & (feature_df['session_hour'] <= 22)
        
        # 2. Session duration categories
        feature_df['short_session'] = feature_df['session_duration'] < 180
        feature_df['medium_session'] = (feature_df['session_duration'] >= 180) & (feature_df['session_duration'] <= 600)
        feature_df['long_session'] = feature_df['session_duration'] > 600
        
        # 3. Typing speed categories
        typing_mean = feature_df['typing_speed'].mean()
        feature_df['slow_typing'] = feature_df['typing_speed'] < (typing_mean * 0.7)
        feature_df['fast_typing'] = feature_df['typing_speed'] > (typing_mean * 1.3)
        
        # 4. Screen aspect ratio
        feature_df['aspect_ratio'] = feature_df['screen_height'] / (feature_df['screen_width'] + 1)
        
        # 5. Location stability (distance from mean)
        if len(behaviors) > 1:
            mean_lat = feature_df['location_lat'].mean()
            mean_lng = feature_df['location_lng'].mean()
            feature_df['location_deviation'] = np.sqrt(
                (feature_df['location_lat'] - mean_lat)**2 + 
                (feature_df['location_lng'] - mean_lng)**2
            )
        else:
            feature_df['location_deviation'] = 0
        
        # Convert boolean to int
        bool_cols = feature_df.select_dtypes(include=['bool']).columns
        feature_df[bool_cols] = feature_df[bool_cols].astype(int)
        
        # Fill NaN values
        feature_df = feature_df.fillna(0)
        
        return feature_df
    
    def train(self, behaviors, contamination=0.1):
        """
        Train Isolation Forest model on user's behavior data
        
        Args:
            behaviors: List of behavior dictionaries
            contamination: Expected proportion of outliers (default 0.1 = 10%)
        
        Returns:
            Dictionary with training results
        """
        if len(behaviors) < 10:
            return {
                'success': False,
                'error': 'Need at least 10 behavior samples to train model',
                'samples_provided': len(behaviors)
            }
        
        try:
            # Engineer features
            feature_df = self.engineer_features(behaviors)
            
            # Initialize scaler
            self.scaler = StandardScaler()
            scaled_features = self.scaler.fit_transform(feature_df)
            
            # Initialize and train Isolation Forest
            self.model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                max_features=1.0,
                bootstrap=False,
                n_jobs=-1,
                verbose=0
            )
            
            self.model.fit(scaled_features)
            
            # Save model and scaler
            os.makedirs('ml_models', exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            # Get training scores
            anomaly_scores = self.model.score_samples(scaled_features)
            predictions = self.model.predict(scaled_features)
            
            # Calculate statistics
            n_anomalies = np.sum(predictions == -1)
            anomaly_percentage = (n_anomalies / len(predictions)) * 100
            
            return {
                'success': True,
                'message': 'Model trained successfully',
                'training_samples': len(behaviors),
                'features_used': len(feature_df.columns),
                'anomalies_detected': int(n_anomalies),
                'anomaly_percentage': round(anomaly_percentage, 2),
                'avg_score': round(float(np.mean(anomaly_scores)), 4),
                'model_saved': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                return True
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def predict(self, current_behavior, recent_behaviors=None):
        """
        Predict if current behavior is anomalous
        
        Args:
            current_behavior: Dictionary with current behavior data
            recent_behaviors: List of recent behaviors for context (optional)
        
        Returns:
            Dictionary with prediction results
        """
        # Try to load existing model
        if self.model is None:
            model_loaded = self.load_model()
            if not model_loaded:
                return {
                    'success': False,
                    'error': 'No trained model available',
                    'anomaly_score': 0,
                    'is_anomaly': False
                }
        
        try:
            # Combine current with recent for context
            if recent_behaviors:
                behaviors = recent_behaviors + [current_behavior]
            else:
                behaviors = [current_behavior]
            
            # Engineer features
            feature_df = self.engineer_features(behaviors)
            
            # Use only the last row (current behavior)
            current_features = feature_df.iloc[[-1]]
            
            # Scale features
            scaled_features = self.scaler.transform(current_features)
            
            # Get anomaly score
            anomaly_score = self.model.score_samples(scaled_features)[0]
            
            # Get prediction (-1 = anomaly, 1 = normal)
            prediction = self.model.predict(scaled_features)[0]
            is_anomaly = (prediction == -1)
            
            # Convert score to 0-100 scale (more intuitive)
            # Isolation Forest scores are typically between -0.5 and 0.5
            # Negative scores = anomalies, Positive = normal
            normalized_score = self._normalize_anomaly_score(anomaly_score)
            
            return {
                'success': True,
                'anomaly_score': round(normalized_score, 2),
                'is_anomaly': bool(is_anomaly),
                'raw_score': round(float(anomaly_score), 4),
                'confidence': self._calculate_confidence(anomaly_score)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'anomaly_score': 0,
                'is_anomaly': False
            }
    
    def _normalize_anomaly_score(self, raw_score):
        """
        Normalize Isolation Forest score to 0-100 scale
        
        Lower raw scores = higher anomaly = higher normalized score
        
        Args:
            raw_score: Raw score from Isolation Forest (typically -0.5 to 0.5)
        
        Returns:
            Normalized score (0-100)
        """
        # Typical range: -0.5 (very anomalous) to 0.5 (very normal)
        # Map to 0-100 where 100 = very anomalous
        
        if raw_score >= 0:
            # Normal behavior (0 to 0.5) -> Low anomaly score (0-30)
            normalized = max(0, 30 - (raw_score * 60))
        else:
            # Anomalous behavior (-0.5 to 0) -> High anomaly score (30-100)
            normalized = 30 + (abs(raw_score) * 140)
        
        return min(100, max(0, normalized))
    
    def _calculate_confidence(self, raw_score):
        """Calculate confidence level based on distance from decision boundary"""
        # Distance from 0 indicates confidence
        confidence = min(abs(raw_score) * 200, 100)
        return round(confidence, 2)
    
    def get_model_info(self):
        """Get information about the trained model"""
        if self.model is None:
            model_loaded = self.load_model()
            if not model_loaded:
                return {
                    'exists': False,
                    'message': 'No trained model available'
                }
        
        try:
            model_stats = {
                'exists': True,
                'n_estimators': self.model.n_estimators,
                'contamination': self.model.contamination,
                'max_samples': self.model.max_samples,
                'features_count': len(self.feature_names),
                'model_path': self.model_path
            }
            
            # Check file size
            if os.path.exists(self.model_path):
                model_stats['file_size_kb'] = round(os.path.getsize(self.model_path) / 1024, 2)
            
            return model_stats
            
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }
    
    def retrain_check(self, total_behaviors):
        """
        Check if model should be retrained
        
        Returns True if:
        - Every 20 new behaviors after initial training
        """
        if total_behaviors < 10:
            return False
        
        # Retrain every 20 behaviors
        return (total_behaviors % 20 == 0)
    
    @staticmethod
    def cleanup_old_models(user_id):
        """Remove old model files for a user"""
        try:
            model_path = f'ml_models/user_{user_id}_model.joblib'
            scaler_path = f'ml_models/user_{user_id}_scaler.joblib'
            
            if os.path.exists(model_path):
                os.remove(model_path)
            if os.path.exists(scaler_path):
                os.remove(scaler_path)
            
            return True
        except Exception as e:
            print(f"Error cleaning up models: {e}")
            return False