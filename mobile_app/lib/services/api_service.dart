import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/constants.dart';
import '../models/user_model.dart';
import '../models/behavior_model.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;

  // =====================================================
  // INIT (MUST BE CALLED ON APP START)
  // =====================================================
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(AppConstants.tokenKey);
    print('🔐 Token loaded on init: ${_token != null}');
  }

  // =====================================================
  // TOKEN STORAGE
  // =====================================================
  Future<void> saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.tokenKey, token);
    print('✅ Token saved');
  }

  Future<void> clearToken() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.tokenKey);
    print('🧹 Token cleared');
  }

  // =====================================================
  // HEADERS (SAFE + BULLETPROOF)
  // =====================================================
  Future<Map<String, String>> _getHeaders({bool needsAuth = false}) async {
    final headers = {
      'Content-Type': 'application/json',
    };

    if (needsAuth) {
      if (_token == null) {
        final prefs = await SharedPreferences.getInstance();
        _token = prefs.getString(AppConstants.tokenKey);
      }

      if (_token != null) {
        headers['Authorization'] = 'Bearer $_token';
      }
    }

    return headers;
  }

  // =====================================================
  // RESPONSE HANDLER (SAFE)
  // =====================================================
  Map<String, dynamic> _handleResponse(http.Response response) {
    final body = json.decode(response.body);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    final message = body['error'] ?? body['message'] ?? 'Request failed';

    throw Exception(message);
  }

  // =====================================================
  // AUTH APIs
  // =====================================================
  Future<Map<String, dynamic>> register(String email, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse('${AppConstants.baseUrl}/api/auth/register'),
            headers: await _getHeaders(),
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
            headers: await _getHeaders(),
            body: json.encode({
              'email': email,
              'password': password,
            }),
          )
          .timeout(AppConstants.apiTimeout);

      final data = _handleResponse(response);

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
            headers: await _getHeaders(needsAuth: true),
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
      await http.post(
        Uri.parse('${AppConstants.baseUrl}/api/auth/logout'),
        headers: await _getHeaders(needsAuth: true),
      );
    } finally {
      await clearToken();
    }
  }

  // =====================================================
  // BEHAVIOR APIs
  // =====================================================
  Future<Map<String, dynamic>> logBehavior(BehaviorData behavior) async {
    final response = await http.post(
      Uri.parse('${AppConstants.baseUrl}/api/behavior/log'),
      headers: await _getHeaders(needsAuth: true),
      body: json.encode(behavior.toJson()),
    );

    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> getBaseline() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/api/behavior/baseline'),
      headers: await _getHeaders(needsAuth: true),
    );

    return _handleResponse(response);
  }

  // =====================================================
  // RISK APIs
  // =====================================================
  Future<Map<String, dynamic>> calculateRisk(BehaviorData behavior) async {
    final response = await http.post(
      Uri.parse('${AppConstants.baseUrl}/api/risk/calculate'),
      headers: await _getHeaders(needsAuth: true),
      body: json.encode(behavior.toJson()),
    );

    return _handleResponse(response);
  }

  Future<RiskScore> getCurrentRisk() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/api/risk/current'),
      headers: await _getHeaders(needsAuth: true),
    );

    final data = _handleResponse(response);
    return RiskScore.fromJson(data['risk']);
  }

  Future<List<RiskScore>> getRiskHistory({int limit = 20}) async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/api/risk/history?limit=$limit'),
      headers: await _getHeaders(needsAuth: true),
    );

    final data = _handleResponse(response);
    return (data['risks'] as List).map((e) => RiskScore.fromJson(e)).toList();
  }

  // =====================================================
  // DASHBOARD
  // =====================================================
  Future<DashboardData> getDashboard() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/api/dashboard'),
      headers: await _getHeaders(needsAuth: true),
    );

    final data = _handleResponse(response);
    return DashboardData.fromJson(data);
  }

  // =====================================================
  // ML APIs
  // =====================================================
  Future<Map<String, dynamic>> trainModel() async {
    final response = await http.post(
      Uri.parse('${AppConstants.baseUrl}/api/ml/train'),
      headers: await _getHeaders(needsAuth: true),
    );

    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> getMLStatus() async {
    final response = await http.get(
      Uri.parse('${AppConstants.baseUrl}/api/ml/status'),
      headers: await _getHeaders(needsAuth: true),
    );

    return _handleResponse(response);
  }

  // =====================================================
  // HEALTH CHECK
  // =====================================================
  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('${AppConstants.baseUrl}/api/health'))
          .timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
