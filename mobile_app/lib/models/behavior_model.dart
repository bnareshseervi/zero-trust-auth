import 'package:mobile_app/models/user_model.dart';



// DashboardData Model
class DashboardData {
  final User user;
  final RiskScore? currentRisk;
  final bool baselineCalculated;
  final int totalSessions;
  final bool mlTrained;
  final int totalBehaviors;
  final double avgRiskScore;

  DashboardData({
    required this.user,
    this.currentRisk,
    required this.baselineCalculated,
    required this.totalSessions,
    required this.mlTrained,
    required this.totalBehaviors,
    required this.avgRiskScore,
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    try {
      final dashboard = json['dashboard'];

      if (dashboard == null) {
        throw Exception('Dashboard data is null');
      }

      // Helper function to safely parse int
      int parseInt(dynamic value) {
        if (value == null) return 0;
        if (value is int) return value;
        if (value is double) return value.toInt();
        if (value is String) return int.tryParse(value) ?? 0;
        return 0;
      }

      // Helper function to safely parse double
      double parseDouble(dynamic value) {
        if (value == null) return 0.0;
        if (value is double) return value;
        if (value is int) return value.toDouble();
        if (value is String) return double.tryParse(value) ?? 0.0;
        return 0.0;
      }

      // Helper function to safely parse bool
      bool parseBool(dynamic value) {
        if (value == null) return false;
        if (value is bool) return value;
        if (value is int) return value != 0;
        if (value is String) return value.toLowerCase() == 'true';
        return false;
      }

      return DashboardData(
        user: User.fromJson(dashboard['user'] ?? {}),
        currentRisk: dashboard['current_risk'] != null &&
                dashboard['current_risk']['score'] != null
            ? RiskScore.fromJson(dashboard['current_risk'])
            : null,
        baselineCalculated:
            parseBool(dashboard['baseline_status']?['calculated']),
        totalSessions:
            parseInt(dashboard['baseline_status']?['total_sessions']),
        mlTrained: parseBool(dashboard['ml_status']?['trained']),
        totalBehaviors: parseInt(dashboard['statistics']?['total_behaviors']),
        avgRiskScore: parseDouble(dashboard['statistics']?['avg_risk_score']),
      );
    } catch (e, stackTrace) {
      print('❌ Error parsing dashboard: $e');
      print('📦 Stack trace: $stackTrace');
      print('📦 Raw JSON: $json');
      rethrow;
    }
  }
}


// BehaviorData Model
class BehaviorData {
  final double typingSpeed;
  final double? avgTapPressure;
  final double? locationLat;
  final double? locationLng;
  final String? deviceModel;
  final String? deviceOs;
  final int? screenWidth;
  final int? screenHeight;
  final int sessionHour;
  final int? sessionDuration;

  BehaviorData({
    required this.typingSpeed,
    this.avgTapPressure,
    this.locationLat,
    this.locationLng,
    this.deviceModel,
    this.deviceOs,
    this.screenWidth,
    this.screenHeight,
    required this.sessionHour,
    this.sessionDuration,
  });

 Map<String, dynamic> toJson() {
  return {
    'typing_speed': typingSpeed,
    'avg_tap_pressure': avgTapPressure ?? 0.75,
    'location_lat': locationLat ?? 0.0,
    'location_lng': locationLng ?? 0.0,
    'device_model': deviceModel ?? 'Unknown',
    'device_os': deviceOs ?? 'Unknown',
    'screen_width': screenWidth ?? 1080,  // Keep as int
    'screen_height': screenHeight ?? 2400,  // Keep as int
    'session_hour': sessionHour,  // Keep as int
    'session_duration': sessionDuration ?? 300,  // Keep as int
  };
}
}


// RiskScore Model
class RiskScore {
  final double score;
  final String level;
  final String action;
  final DateTime timestamp;
  final Map<String, double>? deviations;

  RiskScore({
    required this.score,
    required this.level,
    required this.action,
    required this.timestamp,
    this.deviations,
  });

  factory RiskScore.fromJson(Map<String, dynamic> json) {
  // Helper function to safely convert to double
  double toDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0.0;
    return 0.0;
  }

  try {
    return RiskScore(
      score: toDouble(json['score'] ?? json['risk_score']),
      level: json['level'] ?? json['risk_level'] ?? 'UNKNOWN',
      action: json['action'] ?? json['action_taken'] ?? 'ALLOW',
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'])
          : DateTime.now(),
      deviations: json['deviations'] != null
          ? (json['deviations'] as Map<String, dynamic>)
              .map((key, value) => MapEntry(key, toDouble(value)))
          : null,
    );
  } catch (e) {
    print('❌ Error parsing RiskScore: $e');
    print('📦 Raw JSON: $json');
    return RiskScore(
      score: 0,
      level: 'UNKNOWN',
      action: 'ALLOW',
      timestamp: DateTime.now(),
    );
  }
}}