import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/behavior_provider.dart';
import '../utils/constants.dart';
import '../utils/helpers.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.backgroundColor,
      appBar: AppBar(
        title: const Text('Settings'),
        backgroundColor: AppConstants.primaryColor,
        foregroundColor: Colors.white,
      ),
      body: Consumer2<AuthProvider, BehaviorProvider>(
        builder: (context, authProvider, behaviorProvider, child) {
          final user = authProvider.user;

          return SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Profile Section
                Container(
                  color: Colors.white,
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      CircleAvatar(
                        radius: 40,
                        backgroundColor: AppConstants.primaryColor,
                        child: Text(
                          user?.email[0].toUpperCase() ?? 'U',
                          style: const TextStyle(
                            fontSize: 32,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        user?.email ?? 'User',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (user?.createdAt != null)
                        Text(
                          'Member since ${Helpers.formatDate(user!.createdAt!)}',
                          style: const TextStyle(color: Colors.grey),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Tracking Section
                _buildSection(
                  'Behavior Tracking',
                  [
                    SwitchListTile(
                      title: const Text('Auto-Track Behavior'),
                      subtitle: const Text('Log behavior every 30 seconds'),
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
                      activeColor: AppConstants.primaryColor,
                    ),
                    if (behaviorProvider.autoTrackingEnabled)
                      ListTile(
                        leading:
                            const Icon(Icons.info_outline, color: Colors.blue),
                        title: const Text('Background tracking active'),
                        subtitle: const Text(
                            'Behavior is logged automatically every 30 seconds'),
                        dense: true,
                      ),
                  ],
                ),

                // Data & Privacy
                _buildSection(
                  'Data & Privacy',
                  [
                    ListTile(
                      leading: const Icon(Icons.analytics_outlined),
                      title: const Text('View Risk History'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () {
                        Navigator.pushNamed(context, '/risk-history');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.delete_outline,
                          color: Colors.orange),
                      title: const Text('Clear Behavior Data'),
                      subtitle: const Text('Remove all logged behaviors'),
                      onTap: () async {
                        final confirm = await Helpers.showConfirmDialog(
                          context,
                          'Clear Data',
                          'This will remove all your behavior history. Continue?',
                        );
                        if (confirm) {
                          Helpers.showSnackBar(
                            context,
                            'Feature coming soon',
                          );
                        }
                      },
                    ),
                  ],
                ),

                // ML Model
                _buildSection(
                  'Machine Learning',
                  [
                    ListTile(
                      leading: const Icon(Icons.psychology_outlined),
                      title: const Text('ML Model Status'),
                      subtitle: Text(
                        behaviorProvider.dashboardData?.mlTrained ?? false
                            ? 'Trained and active'
                            : 'Not trained yet',
                      ),
                      trailing: Icon(
                        behaviorProvider.dashboardData?.mlTrained ?? false
                            ? Icons.check_circle
                            : Icons.pending,
                        color:
                            behaviorProvider.dashboardData?.mlTrained ?? false
                                ? AppConstants.successColor
                                : Colors.orange,
                      ),
                    ),
                    if (!(behaviorProvider.dashboardData?.mlTrained ?? false))
                      ListTile(
                        leading:
                            const Icon(Icons.info_outline, color: Colors.blue),
                        title: const Text('Collect more data'),
                        subtitle: Text(
                          'Need ${10 - (behaviorProvider.dashboardData?.totalBehaviors ?? 0)} more sessions to train model',
                        ),
                        dense: true,
                      ),
                  ],
                ),

                // About
                _buildSection(
                  'About',
                  [
                    ListTile(
                      leading: const Icon(Icons.info_outlined),
                      title: const Text('App Version'),
                      subtitle: const Text('1.0.0'),
                    ),
                    ListTile(
                      leading: const Icon(Icons.security_outlined),
                      title: const Text('Zero Trust Authentication'),
                      subtitle:
                          const Text('AI-powered continuous authentication'),
                    ),
                    ListTile(
                      leading: const Icon(Icons.code_outlined),
                      title: const Text('Technology Stack'),
                      subtitle:
                          const Text('Flutter, Python, ML (Isolation Forest)'),
                    ),
                  ],
                ),

                // Account Actions
                _buildSection(
                  'Account',
                  [
                    ListTile(
                      leading:
                          const Icon(Icons.logout, color: Colors.redAccent),
                      title: const Text(
                        'Logout',
                        style: TextStyle(color: Colors.redAccent),
                      ),
                      onTap: () async {
                        final confirm = await Helpers.showConfirmDialog(
                          context,
                          'Logout',
                          'Are you sure you want to logout?',
                        );

                        if (confirm) {
                          await authProvider.logout();
                          if (context.mounted) {
                            Navigator.pushReplacementNamed(context, '/login');
                          }
                        }
                      },
                    ),
                  ],
                ),

                const SizedBox(height: 32),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Colors.grey,
            ),
          ),
        ),
        Container(
          color: Colors.white,
          child: Column(children: children),
        ),
      ],
    );
  }
}
