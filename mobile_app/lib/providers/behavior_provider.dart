import 'package:flutter/material.dart';
import 'dart:async';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:geolocator/geolocator.dart';
import 'dart:io';
import '../models/behavior_model.dart';
import '../services/api_service.dart';
import '../services/background_tracker.dart';

class BehaviorProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();

  DashboardData? _dashboardData;
  RiskScore? _currentRisk;
  bool _isLoading = false;
  String? _error;
  BackgroundTracker? _backgroundTracker;
  bool _autoTrackingEnabled = false;

  // Behavior tracking
  double _currentTypingSpeed = 60.0;
  String? _deviceModel;
  String? _deviceOs;
  int? _screenWidth;
  int? _screenHeight;
  Position? _lastPosition;

  // Getters
  DashboardData? get dashboardData => _dashboardData;
  RiskScore? get currentRisk => _currentRisk;
  bool get isLoading => _isLoading;
  bool get autoTrackingEnabled => _autoTrackingEnabled;
  String? get error => _error;
  double get currentTypingSpeed => _currentTypingSpeed;

  BehaviorProvider() {
    _initDeviceInfo();
  }
  // Initialize auto-tracking
  void initAutoTracking() {
    _backgroundTracker = BackgroundTracker(
      onTrack: () async {
        print('📊 Auto-logging behavior...');
        await logBehavior();
      },
    );
  }

  // Initialize device information
  Future<void> _initDeviceInfo() async {
    try {
      final deviceInfo = DeviceInfoPlugin();

      if (Platform.isAndroid) {
        final androidInfo = await deviceInfo.androidInfo;
        _deviceModel = androidInfo.model;
        _deviceOs = 'Android ${androidInfo.version.release}';
      } else if (Platform.isIOS) {
        final iosInfo = await deviceInfo.iosInfo;
        _deviceModel = iosInfo.model;
        _deviceOs = 'iOS ${iosInfo.systemVersion}';
      }

      // Get screen size (approximate)
      _screenWidth = 1080;
      _screenHeight = 2400;
    } catch (e) {
      print('Failed to get device info: $e');
    }
  }

  // Start auto-tracking
  void startAutoTracking() {
    if (_backgroundTracker == null) {
      initAutoTracking();
    }
    _backgroundTracker?.startTracking();
    _autoTrackingEnabled = true;
    notifyListeners();
  }

// Stop auto-tracking
  void stopAutoTracking() {
    _backgroundTracker?.stopTracking();
    _autoTrackingEnabled = false;
    notifyListeners();
  }

// Toggle auto-tracking
  void toggleAutoTracking() {
    if (_autoTrackingEnabled) {
      stopAutoTracking();
    } else {
      startAutoTracking();
    }
  }

// Override dispose
  @override
  void dispose() {
    _backgroundTracker?.dispose();
    super.dispose();
  }

  // Get location
  Future<void> _updateLocation() async {
    try {
      // Check permission
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }

      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        // Use default location if denied
        return;
      }

      _lastPosition = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.low,
      );
    } catch (e) {
      print('Failed to get location: $e');
    }
  }

  // Update typing speed
  void updateTypingSpeed(double speed) {
    _currentTypingSpeed = speed;
  }

  // Create behavior data
  Future<BehaviorData> _createBehaviorData() async {
    await _updateLocation();

    return BehaviorData(
      typingSpeed: _currentTypingSpeed,
      avgTapPressure: 0.75,
      locationLat: _lastPosition?.latitude,
      locationLng: _lastPosition?.longitude,
      deviceModel: _deviceModel,
      deviceOs: _deviceOs,
      screenWidth: _screenWidth,
      screenHeight: _screenHeight,
      sessionHour: DateTime.now().hour,
      sessionDuration: 300,
    );
  }

  // Log behavior
  Future<bool> logBehavior() async {
    try {
      final behavior = await _createBehaviorData();
      await _apiService.logBehavior(behavior);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  // Calculate risk
  Future<void> calculateRisk() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final behavior = await _createBehaviorData();
      final response = await _apiService.calculateRisk(behavior);

      if (response['success']) {
        _currentRisk = RiskScore(
          score: (response['risk_score'] ?? 0).toDouble(),
          level: response['risk_level'] ?? 'UNKNOWN',
          action: response['action'] ?? 'ALLOW',
          timestamp: DateTime.now(),
          deviations: response['deviations'] != null
              ? Map<String, double>.from(response['deviations'])
              : null,
        );
      }
    } catch (e) {
      _error = e.toString().replaceAll('Exception: ', '');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Fetch dashboard data
  Future<void> fetchDashboard() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      print('🔵 BehaviorProvider: Fetching dashboard...');
      _dashboardData = await _apiService.getDashboard();
      print('✅ BehaviorProvider: Dashboard fetched successfully');

      // Update current risk from dashboard
      if (_dashboardData?.currentRisk != null) {
        _currentRisk = _dashboardData!.currentRisk;
      }
    } catch (e) {
      print('❌ BehaviorProvider: Dashboard fetch failed: $e');
      _error = e.toString().replaceAll('Exception: ', '');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Get baseline
  Future<Map<String, dynamic>?> getBaseline() async {
    try {
      return await _apiService.getBaseline();
    } catch (e) {
      return null;
    }
  }

  // Train ML model
  Future<bool> trainMLModel() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiService.trainModel();
      _isLoading = false;
      notifyListeners();
      return response['success'] ?? false;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Get ML status
  Future<Map<String, dynamic>?> getMLStatus() async {
    try {
      return await _apiService.getMLStatus();
    } catch (e) {
      return null;
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }

  // Reset all data
  void reset() {
    _dashboardData = null;
    _currentRisk = null;
    _error = null;
    notifyListeners();
  }
}
