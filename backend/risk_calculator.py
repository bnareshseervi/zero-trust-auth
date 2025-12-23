import math
from datetime import datetime

class RiskCalculator:
    """Calculate risk scores based on behavioral deviations"""
    
    # Weight factors for different risk components
    WEIGHTS = {
        'typing': 0.30,
        'location': 0.25,
        'time': 0.20,
        'device': 0.25
    }
    
    @staticmethod
    def calculate_risk_with_ml(current_behavior, baseline, recent_behaviors, ml_score):
        """
        Enhanced risk calculation including ML anomaly score
        
        Args:
            current_behavior: Current behavior dict
            baseline: Baseline dict
            recent_behaviors: List of recent behaviors
            ml_score: ML anomaly score (0-100)
        
        Returns:
            Enhanced risk result dict
        """
        # Get base risk calculation
        base_risk = RiskCalculator.calculate_risk(
            current_behavior, baseline, recent_behaviors
        )
        
        # Integrate ML score (30% weight)
        ml_weight = 0.30
        base_weight = 0.70
        
        # Combined risk score
        combined_score = (base_risk['risk_score'] * base_weight) + (ml_score * ml_weight)
        
        # Update risk level and action based on combined score
        combined_level = RiskCalculator.get_risk_level(combined_score)
        combined_action = RiskCalculator.get_action(combined_score)
        
        return {
            'risk_score': round(combined_score, 2),
            'risk_level': combined_level,
            'action_taken': combined_action,
            'typing_deviation': base_risk['typing_deviation'],
            'location_deviation': base_risk['location_deviation'],
            'time_deviation': base_risk['time_deviation'],
            'device_deviation': base_risk['device_deviation'],
            'ml_anomaly_score': round(ml_score, 2),
            'base_risk_score': base_risk['risk_score'],
            'ml_contribution': round(ml_score * ml_weight, 2)
        }
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS coordinates (Haversine formula)"""
        if not all([lat1, lon1, lat2, lon2]):
            return 0
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        r = 6371
        return c * r
    
    @staticmethod
    def calculate_typing_deviation(current_speed, baseline_speed, std_dev):
        """Calculate typing speed deviation score (0-100)"""
        if not baseline_speed or baseline_speed == 0:
            return 0
        
        # Calculate absolute deviation
        deviation = abs(current_speed - baseline_speed)
        
        # Normalize using standard deviation
        if std_dev and std_dev > 0:
            normalized_deviation = deviation / std_dev
        else:
            # If no std_dev, use percentage difference
            normalized_deviation = deviation / baseline_speed
        
        # Convert to 0-100 scale (cap at 100)
        score = min(normalized_deviation * 30, 100)
        return score
    
    @staticmethod
    def calculate_location_deviation(current_lat, current_lng, baseline_lat, baseline_lng):
        """Calculate location deviation score (0-100)"""
        if not all([current_lat, current_lng, baseline_lat, baseline_lng]):
            return 0
        
        # Calculate distance in km
        distance = RiskCalculator.calculate_distance(
            current_lat, current_lng, baseline_lat, baseline_lng
        )
        
        # Convert to risk score
        # 0 km = 0 risk
        # 50 km = 25 risk
        # 200 km = 50 risk
        # 500+ km = 100 risk
        if distance < 10:
            score = 0
        elif distance < 50:
            score = (distance - 10) / 40 * 25
        elif distance < 200:
            score = 25 + (distance - 50) / 150 * 25
        elif distance < 500:
            score = 50 + (distance - 200) / 300 * 50
        else:
            score = 100
        
        return min(score, 100)
    
    @staticmethod
    def calculate_time_deviation(current_hour, baseline_hour):
        """Calculate time deviation score (0-100)"""
        if baseline_hour is None or current_hour is None:
            return 0
        
        # Calculate hour difference (considering 24-hour wrap)
        diff = abs(current_hour - baseline_hour)
        if diff > 12:
            diff = 24 - diff
        
        # Convert to risk score
        # 0-2 hours difference = 0 risk
        # 3-5 hours = 25 risk
        # 6-8 hours = 50 risk
        # 9+ hours = 100 risk
        if diff <= 2:
            score = 0
        elif diff <= 5:
            score = (diff - 2) / 3 * 25
        elif diff <= 8:
            score = 25 + (diff - 5) / 3 * 25
        else:
            score = 50 + (diff - 8) / 4 * 50
        
        return min(score, 100)
    
    @staticmethod
    def calculate_device_deviation(current_device, current_os, baseline_behaviors):
        """Calculate device change score (0-100)"""
        if not baseline_behaviors or not current_device:
            return 0
        
        # Check if device/OS has been seen before
        device_seen = any(
            b.get('device_model') == current_device and b.get('device_os') == current_os
            for b in baseline_behaviors
        )
        
        # If new device/OS combination = high risk
        if not device_seen:
            return 80
        
        # If same device = no risk
        return 0
    
    @staticmethod
    def calculate_overall_risk(deviations):
        """Calculate overall risk score from individual deviations"""
        typing_score = deviations.get('typing', 0)
        location_score = deviations.get('location', 0)
        time_score = deviations.get('time', 0)
        device_score = deviations.get('device', 0)
        
        # Weighted sum
        overall = (
            typing_score * RiskCalculator.WEIGHTS['typing'] +
            location_score * RiskCalculator.WEIGHTS['location'] +
            time_score * RiskCalculator.WEIGHTS['time'] +
            device_score * RiskCalculator.WEIGHTS['device']
        )
        
        return min(overall, 100)
    
    @staticmethod
    def get_risk_level(score):
        """Determine risk level from score"""
        if score < 30:
            return 'LOW'
        elif score < 60:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    @staticmethod
    def get_action(score):
        """Determine action based on risk score"""
        if score < 30:
            return 'ALLOW'
        elif score < 60:
            return 'WARN'
        else:
            return 'BLOCK'
    
    @staticmethod
    def calculate_risk(current_behavior, baseline, recent_behaviors=None):
        """
        Main function to calculate risk score
        
        Args:
            current_behavior: Dict with current behavior data
            baseline: Dict with baseline behavior data
            recent_behaviors: List of recent behavior dicts (optional)
        
        Returns:
            Dict with risk score and details
        """
        deviations = {}
        
        # Calculate typing deviation
        deviations['typing'] = RiskCalculator.calculate_typing_deviation(
            current_behavior.get('typing_speed', 0),
            baseline.get('avg_typing_speed', 0),
            baseline.get('std_typing_speed', 0)
        )
        
        # Calculate location deviation
        deviations['location'] = RiskCalculator.calculate_location_deviation(
            current_behavior.get('location_lat'),
            current_behavior.get('location_lng'),
            baseline.get('common_location_lat'),
            baseline.get('common_location_lng')
        )
        
        # Calculate time deviation
        current_hour = current_behavior.get('session_hour')
        if current_hour is None:
            current_hour = datetime.now().hour
        
        deviations['time'] = RiskCalculator.calculate_time_deviation(
            current_hour,
            baseline.get('common_session_hour')
        )
        
        # Calculate device deviation
        deviations['device'] = RiskCalculator.calculate_device_deviation(
            current_behavior.get('device_model'),
            current_behavior.get('device_os'),
            recent_behaviors
        )
        
        # Calculate overall risk
        risk_score = RiskCalculator.calculate_overall_risk(deviations)
        risk_level = RiskCalculator.get_risk_level(risk_score)
        action = RiskCalculator.get_action(risk_score)
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'action_taken': action,
            'typing_deviation': round(deviations['typing'], 2),
            'location_deviation': round(deviations['location'], 2),
            'time_deviation': round(deviations['time'], 2),
            'device_deviation': round(deviations['device'], 2),
            'ml_anomaly_score': 0  # Will be updated when ML is used
        }