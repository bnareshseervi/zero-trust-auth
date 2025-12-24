import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';
import '../models/user_model.dart';
import '../models/behavior_model.dart';
// REMOVED: import '../models/risk_model.dart'; - Now in behavior_model.dart

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;

  // Initialize token from storage
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(AppConstants.tokenKey);
  }

  // Save token to storage
  Future<void> saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.tokenKey, token);
  }

  // Clear token
  Future<void> clearToken() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.tokenKey);
  }

  // Get headers
  Map<String, String> _getHeaders({bool needsAuth = false}) {
    final headers = {
      'Content-Type': 'application/json',
    };

    if (needsAuth && _token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }

    return headers;
  }

  // Handle response
  Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return json.decode(response.body);
    } else {
      final error = json.decode(response.body);
      throw Exception(error['error'] ?? 'Request failed');
    }
  }

  // ============================================
  // AUTHENTICATION APIs
  // ============================================

  Future<Map<String, dynamic>> register(String email, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/api/auth/register'),
            headers: _getHeaders(),
            body: json.encode({
              'email': email,
              'password': password,
            }),
          )
          .timeout(AppConstants.apiTimeout);

      return _handleResponse(response);
    } catch (e) {
      throw Exception('Registration failed: $e');
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/api/auth/login'),
            headers: _getHeaders(),
            body: json.encode({
              'email': email,
              'password': password,
            }),
          )
          .timeout(AppConstants.apiTimeout);

      final data = _handleResponse(response);

      // Save token
      if (data['token'] != null) {
        await saveToken(data['token']);
      }

      return data;
    } catch (e) {
      throw Exception('Login failed: $e');
    }
  }

  Future<User> getProfile() async {
    try {
      final response = await http
          .get(
            Uri.parse('${AppConstants.baseUrl}/api/auth/profile'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      final data = _handleResponse(response);
      return User.fromJson(data['user']);
    } catch (e) {
      throw Exception('Failed to get profile: $e');
    }
  }

  Future<void> logout() async {
    try {
      await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/api/auth/logout'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      await clearToken();
    } catch (e) {
      // Clear token anyway
      await clearToken();
      throw Exception('Logout failed: $e');
    }
  }

  // ============================================
  // BEHAVIOR APIs
  // ============================================

  Future<Map<String, dynamic>> logBehavior(BehaviorData behavior) async {
    try {
      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/api/behavior/log'),
            headers: _getHeaders(needsAuth: true),
            body: json.encode(behavior.toJson()),
          )
          .timeout(AppConstants.apiTimeout);

      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to log behavior: $e');
    }
  }

  Future<Map<String, dynamic>> getBaseline() async {
    try {
      final response = await http
          .get(
            Uri.parse('${AppConstants.baseUrl}/api/behavior/baseline'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to get baseline: $e');
    }
  }

  // ============================================
  // RISK APIs
  // ============================================

  Future<Map<String, dynamic>> calculateRisk(BehaviorData behavior) async {
    try {
      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/api/risk/calculate'),
            headers: _getHeaders(needsAuth: true),
            body: json.encode(behavior.toJson()),
          )
          .timeout(AppConstants.apiTimeout);

      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to calculate risk: $e');
    }
  }

  Future<RiskScore> getCurrentRisk() async {
    try {
      final response = await http
          .get(
            Uri.parse('${AppConstants.baseUrl}/api/risk/current'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      final data = _handleResponse(response);
      return RiskScore.fromJson(data['risk']);
    } catch (e) {
      throw Exception('Failed to get current risk: $e');
    }
  }

  Future<List<RiskScore>> getRiskHistory({int limit = 20}) async {
    try {
      final response = await http
          .get(
            Uri.parse('${AppConstants.baseUrl}/api/risk/history?limit=$limit'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      final data = _handleResponse(response);
      final risks = data['risks'] as List;
      return risks.map((r) => RiskScore.fromJson(r)).toList();
    } catch (e) {
      throw Exception('Failed to get risk history: $e');
    }
  }

  // ============================================
  // DASHBOARD API
  // ============================================

  Future<DashboardData> getDashboard() async {
    try {
      print(
          '📊 Fetching dashboard from: ${AppConstants.baseUrl}/api/dashboard');
      print('📊 Token exists: ${_token != null}');

      final response = await http
          .get(
            Uri.parse('${AppConstants.baseUrl}/api/dashboard'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      print('📊 Dashboard response status: ${response.statusCode}');
      print('📊 Dashboard response body: ${response.body}');

      final data = _handleResponse(response);

      print('✅ Dashboard data received, parsing...');
      return DashboardData.fromJson(data);
    } catch (e) {
      print('❌ Dashboard error: $e');
      throw Exception('Failed to get dashboard: $e');
    }
  }

  // ============================================
  // ML APIs
  // ============================================

  Future<Map<String, dynamic>> trainModel() async {
    try {
      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/api/ml/train'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to train model: $e');
    }
  }

  Future<Map<String, dynamic>> getMLStatus() async {
    try {
      final response = await http
          .get(
            Uri.parse('${AppConstants.baseUrl}/api/ml/status'),
            headers: _getHeaders(needsAuth: true),
          )
          .timeout(AppConstants.apiTimeout);

      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to get ML status: $e');
    }
  }

  // ============================================
  // HEALTH CHECK
  // ============================================

  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(
            Uri.parse('${AppConstants.baseUrl}/api/health'),
          )
          .timeout(Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
