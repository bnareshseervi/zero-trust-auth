import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

class AuthProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  User? _user;
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _error;
  
  User? get user => _user;
  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  AuthProvider() {
    _checkAuthStatus();
  }
  
  // Check if user is already logged in
  Future<void> _checkAuthStatus() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      await _apiService.init();
      
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString(AppConstants.tokenKey);
      
      if (token != null) {
        // Try to fetch user profile
        try {
          _user = await _apiService.getProfile();
          _isAuthenticated = true;
        } catch (e) {
          // Token invalid, clear it
          await _apiService.clearToken();
          _isAuthenticated = false;
        }
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // Register new user
  Future<bool> register(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.register(email, password);
      
      if (response['success']) {
        // After registration, log in
        return await login(email, password);
      }
      
      return false;
    } catch (e) {
      _error = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // Login user
  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      final response = await _apiService.login(email, password);
      
      if (response['success']) {
        // Save user email
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(AppConstants.userEmailKey, email);
        
        // Fetch user profile
        _user = await _apiService.getProfile();
        _isAuthenticated = true;
        
        _isLoading = false;
        notifyListeners();
        return true;
      }
      
      return false;
    } catch (e) {
      _error = e.toString().replaceAll('Exception: ', '');
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }
  
  // Logout user
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      await _apiService.logout();
    } catch (e) {
      // Ignore errors on logout
    } finally {
      _user = null;
      _isAuthenticated = false;
      _error = null;
      _isLoading = false;
      
      // Clear all stored data
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();
      
      notifyListeners();
    }
  }
  
  // Refresh user profile
  Future<void> refreshProfile() async {
    try {
      _user = await _apiService.getProfile();
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }
  
  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}