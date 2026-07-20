import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/router/role_tabs.dart';
import '../../core/router/routes.dart';
import '../../core/router/screen_registry.dart';
import '../announcements/application/announcements_providers.dart';
import '../auth/application/auth_controller.dart';

/// The authenticated home: a role-based bottom navigation bar over an
/// [IndexedStack] of feature screens. Each tab screen carries its own AppBar.
class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key});

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final role = ref.watch(roleProvider);
    final tabs = tabsForRole(role);
    final unread = ref.watch(unreadCountProvider).valueOrNull ?? 0;

    // Guard against role change shrinking the tab list.
    final index = _index.clamp(0, tabs.length - 1);

    return Scaffold(
      body: IndexedStack(
        index: index,
        children: [
          for (final tab in tabs) screenForRoute(tab.route),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          for (final tab in tabs)
            NavigationDestination(
              icon: _maybeBadge(tab, unread, Icon(tab.icon)),
              selectedIcon: _maybeBadge(tab, unread, Icon(tab.activeIcon)),
              label: tab.label,
            ),
        ],
      ),
    );
  }

  /// Shows an unread count badge on the announcements/notices tab.
  Widget _maybeBadge(TabItem tab, int unread, Widget icon) {
    if (tab.route == Routes.announcements && unread > 0) {
      return Badge(
        label: Text('$unread'),
        child: icon,
      );
    }
    return icon;
  }
}
