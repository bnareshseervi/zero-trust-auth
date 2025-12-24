import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class Helpers {
  // Show snackbar
  static void showSnackBar(BuildContext context, String message,
      {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : Colors.green,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        duration: Duration(seconds: 3),
      ),
    );
  }

  // Format date
  static String formatDate(DateTime date) {
    return DateFormat('MMM dd, yyyy').format(date);
  }

  // Format time
  static String formatTime(DateTime date) {
    return DateFormat('hh:mm a').format(date);
  }

  // Format date and time
  static String formatDateTime(DateTime date) {
    return DateFormat('MMM dd, yyyy hh:mm a').format(date);
  }

  // Validate email
  static bool isValidEmail(String email) {
    return RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email);
  }

  // Show loading dialog
  static void showLoadingDialog(BuildContext context) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Loading...'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Hide loading dialog
  static void hideLoadingDialog(BuildContext context) {
    Navigator.of(context).pop();
  }

  // Show confirmation dialog
  static Future<bool> showConfirmDialog(
    BuildContext context,
    String title,
    String message,
  ) async {
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(title),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text('Confirm'),
              ),
            ],
          ),
        ) ??
        false;
  }

  // Get current hour
  static int getCurrentHour() {
    return DateTime.now().hour;
  }

  // Calculate typing speed (mock for now)
  static double calculateTypingSpeed(String text, Duration duration) {
    if (duration.inSeconds == 0) return 0;
    int wordCount = text.split(' ').length;
    return (wordCount / duration.inMinutes).clamp(0, 150);
  }
}
