import 'dart:async';

class BackgroundTracker {
  static BackgroundTracker? _instance;
  Timer? _timer;
  bool _isTracking = false;

  // Callback for logging behavior
  final Function()? onTrack;

  BackgroundTracker._({this.onTrack});

  factory BackgroundTracker({Function()? onTrack}) {
    _instance ??= BackgroundTracker._(onTrack: onTrack);
    return _instance!;
  }

  bool get isTracking => _isTracking;

  // Start tracking every 30 seconds
  void startTracking() {
    if (_isTracking) return;

    print('🔵 Background tracking started');
    _isTracking = true;

    // Track immediately
    onTrack?.call();

    // Then every 30 seconds
    _timer = Timer.periodic(
      const Duration(seconds: 30),
      (timer) {
        print('⏰ Auto-tracking behavior...');
        onTrack?.call();
      },
    );
  }

  // Stop tracking
  void stopTracking() {
    if (!_isTracking) return;

    print('🔴 Background tracking stopped');
    _isTracking = false;
    _timer?.cancel();
    _timer = null;
  }

  // Toggle tracking
  void toggleTracking() {
    if (_isTracking) {
      stopTracking();
    } else {
      startTracking();
    }
  }

  // Cleanup
  void dispose() {
    stopTracking();
  }
}
