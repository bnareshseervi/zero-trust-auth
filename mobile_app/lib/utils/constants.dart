import 'package:flutter/material.dart';

class AppConstants {
  // API Configuration
  static const String baseUrl =
      'https://zero-trust-auth-production-097b.up.railway.app';
  // Use 'http://localhost:5000' for iOS Simulator
  // Use 'http://YOUR_IP:5000' for physical device

  static const Duration apiTimeout = Duration(seconds: 30);

  // Storage Keys
  static const String tokenKey = 'auth_token';
  static const String userEmailKey = 'user_email';
  static const String userIdKey = 'user_id';

  // Risk Levels
  static const double lowRiskThreshold = 30.0;
  static const double mediumRiskThreshold = 60.0;

  // Colors
  static const Color primaryColor = Color(0xFF6366F1);
  static const Color secondaryColor = Color(0xFF8B5CF6);
  static const Color successColor = Color(0xFF10B981);
  static const Color warningColor = Color(0xFFF59E0B);
  static const Color dangerColor = Color(0xFFEF4444);
  static const Color backgroundColor = Color(0xFFF9FAFB);

  // Risk Colors
  static Color getRiskColor(double score) {
    if (score < lowRiskThreshold) {
      return successColor;
    } else if (score < mediumRiskThreshold) {
      return warningColor;
    } else {
      return dangerColor;
    }
  }

  static String getRiskLevel(double score) {
    if (score < lowRiskThreshold) {
      return 'LOW';
    } else if (score < mediumRiskThreshold) {
      return 'MEDIUM';
    } else {
      return 'HIGH';
    }
  }

  // Text Styles
  static const TextStyle headingStyle = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    color: Color(0xFF111827),
  );

  static const TextStyle subheadingStyle = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
    color: Color(0xFF374151),
  );

  static const TextStyle bodyStyle = TextStyle(
    fontSize: 16,
    color: Color(0xFF6B7280),
  );

  // Spacing
  static const double paddingSmall = 8.0;
  static const double paddingMedium = 16.0;
  static const double paddingLarge = 24.0;

  static const double borderRadius = 12.0;
  static const double borderRadiusLarge = 20.0;
}
