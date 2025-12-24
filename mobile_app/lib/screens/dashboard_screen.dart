import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/behavior_provider.dart';
import '../widgets/risk_gauge.dart';
import '../utils/constants.dart';
import '../utils/helpers.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    final behaviorProvider =
        Provider.of<BehaviorProvider>(context, listen: false);

    print('📊 Loading dashboard...');
    await behaviorProvider.fetchDashboard();

    if (behaviorProvider.error != null) {
      print('❌ Dashboard error: ${behaviorProvider.error}');
    } else if (behaviorProvider.dashboardData != null) {
      print('✅ Dashboard loaded successfully');
    } else {
      print('⚠️ Dashboard data is null but no error');
    }
  }

  Future<void> _handleRefresh() async {
    await _loadDashboard();
  }

  Future<void> _calculateRisk() async {
    final behaviorProvider =
        Provider.of<BehaviorProvider>(context, listen: false);

    Helpers.showLoadingDialog(context);
    await behaviorProvider.calculateRisk();
    if (!mounted) return;
    Helpers.hideLoadingDialog(context);

    if (behaviorProvider.error != null) {
      Helpers.showSnackBar(context, behaviorProvider.error!, isError: true);
    } else {
      await _loadDashboard();
      // ignore: use_build_context_synchronously
      Helpers.showSnackBar(context, 'Risk calculated successfully!');
    }
  }

  Future<void> _trainModel() async {
    final behaviorProvider =
        Provider.of<BehaviorProvider>(context, listen: false);

    final confirm = await Helpers.showConfirmDialog(
      context,
      'Train ML Model',
      'This will train the ML model with your behavior history. Continue?',
    );

    if (!confirm) return;

    Helpers.showLoadingDialog(context);
    final success = await behaviorProvider.trainMLModel();
    if (!mounted) return;
    Helpers.hideLoadingDialog(context);

    if (success) {
      await _loadDashboard();
      Helpers.showSnackBar(context, 'ML model trained successfully!');
    } else {
      Helpers.showSnackBar(context, 'Failed to train model', isError: true);
    }
  }

  Future<void> _handleLogout() async {
    final confirm = await Helpers.showConfirmDialog(
      context,
      'Logout',
      'Are you sure you want to logout?',
    );

    if (!confirm) return;

    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    await authProvider.logout();

    if (!mounted) return;
    Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.backgroundColor,
      appBar: AppBar(
        title: const Text('Dashboard'),
        backgroundColor: AppConstants.primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {
              Navigator.pushNamed(context, '/risk-history');
            },
            tooltip: 'Risk History',
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.pushNamed(context, '/settings');
            },
            tooltip: 'Settings',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _handleRefresh,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _handleRefresh,
        child: Consumer<BehaviorProvider>(
          builder: (context, behaviorProvider, child) {
            if (behaviorProvider.isLoading &&
                behaviorProvider.dashboardData == null) {
              return const Center(child: CircularProgressIndicator());
            }

            final dashboard = behaviorProvider.dashboardData;

            if (dashboard == null) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.cloud_off,
                        size: 64,
                        color: Colors.grey,
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'Failed to load dashboard',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (behaviorProvider.error != null)
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text(
                            behaviorProvider.error!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: Colors.grey,
                              fontSize: 14,
                            ),
                          ),
                        ),
                      const SizedBox(height: 24),
                      ElevatedButton.icon(
                        onPressed: _handleRefresh,
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retry'),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 32,
                            vertical: 16,
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextButton(
                        onPressed: _handleLogout,
                        child: const Text('Logout and try again'),
                      ),
                    ],
                  ),
                ),
              );
            }

            final currentRisk = dashboard.currentRisk;
            final riskScore = currentRisk?.score ?? 0.0;

            return SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(AppConstants.paddingMedium),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Welcome Card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(AppConstants.paddingMedium),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 30,
                            backgroundColor: AppConstants.primaryColor,
                            child: Text(
                              dashboard.user.email[0].toUpperCase(),
                              style: const TextStyle(
                                fontSize: 24,
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Welcome back!',
                                  style: TextStyle(
                                    fontSize: 16,
                                    color: Colors.grey,
                                  ),
                                ),
                                Text(
                                  dashboard.user.email,
                                  style: const TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Risk Score Gauge
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(AppConstants.paddingLarge),
                      child: Column(
                        children: [
                          const Text(
                            'Current Risk Level',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 24),
                          RiskGauge(score: riskScore),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: _calculateRisk,
                            icon: const Icon(Icons.calculate),
                            label: const Text('Calculate Risk Now'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppConstants.primaryColor,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 24,
                                vertical: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Statistics Cards
                  Row(
                    children: [
                      Expanded(
                        child: _StatCard(
                          title: 'Total Sessions',
                          value: dashboard.totalBehaviors.toString(),
                          icon: Icons.history,
                          color: Colors.blue,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _StatCard(
                          title: 'Avg Risk',
                          value: dashboard.avgRiskScore.toStringAsFixed(0),
                          icon: Icons.trending_up,
                          color:
                              AppConstants.getRiskColor(dashboard.avgRiskScore),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _StatCard(
                          title: 'Baseline',
                          value: dashboard.baselineCalculated
                              ? 'Ready'
                              : 'Learning',
                          icon: Icons.analytics,
                          color: dashboard.baselineCalculated
                              ? AppConstants.successColor
                              : AppConstants.warningColor,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _StatCard(
                          title: 'ML Model',
                          value: dashboard.mlTrained ? 'Trained' : 'Not Ready',
                          icon: Icons.psychology,
                          color: dashboard.mlTrained
                              ? AppConstants.successColor
                              : Colors.orange,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // ML Training Card
                  if (!dashboard.mlTrained && dashboard.totalBehaviors >= 10)
                    Card(
                      color: Colors.orange[50],
                      child: Padding(
                        padding:
                            const EdgeInsets.all(AppConstants.paddingMedium),
                        child: Column(
                          children: [
                            Row(
                              children: [
                                Icon(Icons.auto_awesome,
                                    color: Colors.orange[700]),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'Ready to train ML model!',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Colors.orange[900],
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'You have enough data to train the AI model for better anomaly detection.',
                              style: TextStyle(color: Colors.orange[800]),
                            ),
                            const SizedBox(height: 12),
                            ElevatedButton(
                              onPressed: _trainModel,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.orange,
                                foregroundColor: Colors.white,
                              ),
                              child: const Text('Train Model'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  // Auto-Tracking Card
                  Card(
                    color: behaviorProvider.autoTrackingEnabled
                        ? Colors.green[50]
                        : Colors.grey[50],
                    child: Padding(
                      padding: const EdgeInsets.all(AppConstants.paddingMedium),
                      child: Row(
                        children: [
                          Icon(
                            behaviorProvider.autoTrackingEnabled
                                ? Icons.check_circle
                                : Icons.circle_outlined,
                            color: behaviorProvider.autoTrackingEnabled
                                ? AppConstants.successColor
                                : Colors.grey,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  behaviorProvider.autoTrackingEnabled
                                      ? 'Auto-Tracking Active'
                                      : 'Auto-Tracking Disabled',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: behaviorProvider.autoTrackingEnabled
                                        ? Colors.green[900]
                                        : Colors.grey[700],
                                  ),
                                ),
                                Text(
                                  behaviorProvider.autoTrackingEnabled
                                      ? 'Logging behavior every 30 seconds'
                                      : 'Enable in settings for automatic tracking',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: behaviorProvider.autoTrackingEnabled
                                        ? Colors.green[700]
                                        : Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Switch(
                            value: behaviorProvider.autoTrackingEnabled,
                            onChanged: (value) {
                              behaviorProvider.toggleAutoTracking();
                              Helpers.showSnackBar(
                                context,
                                value
                                    ? 'Auto-tracking enabled'
                                    : 'Auto-tracking disabled',
                              );
                            },
                            activeColor: AppConstants.successColor,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Info Card
                  if (dashboard.totalBehaviors < 5)
                    Card(
                      color: Colors.blue[50],
                      child: Padding(
                        padding:
                            const EdgeInsets.all(AppConstants.paddingMedium),
                        child: Row(
                          children: [
                            Icon(Icons.info_outline, color: Colors.blue[700]),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Need ${5 - dashboard.totalBehaviors} more sessions to calculate baseline',
                                style: TextStyle(color: Colors.blue[900]),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
