import 'package:flutter/material.dart';

import '../../features/auth/domain/app_role.dart';
import 'routes.dart';

/// A bottom-nav destination.
class TabItem {
  const TabItem({
    required this.label,
    required this.icon,
    required this.activeIcon,
    required this.route,
  });

  final String label;
  final IconData icon;
  final IconData activeIcon;

  /// The feature route this tab points at (used to resolve the body widget).
  final String route;
}

/// An entry in the "More" menu.
class ModuleEntry {
  const ModuleEntry({
    required this.title,
    required this.icon,
    required this.route,
    this.permission,
    this.roles,
  });

  final String title;
  final IconData icon;
  final String route;

  /// `module:action` permission required to see this entry (null = always).
  final String? permission;

  /// Roles allowed to see this entry (null = all).
  final List<AppRole>? roles;
}

// ─── Per-role bottom tabs (mirrors mobile/app/(app)/_layout.tsx) ────────────

const _adminTabs = <TabItem>[
  TabItem(label: 'Dashboard', icon: Icons.grid_view_outlined, activeIcon: Icons.grid_view, route: Routes.dashboard),
  TabItem(label: 'Students', icon: Icons.people_outline, activeIcon: Icons.people, route: Routes.students),
  TabItem(label: 'Staff', icon: Icons.person_outline, activeIcon: Icons.person, route: Routes.staff),
  TabItem(label: 'Fees', icon: Icons.account_balance_wallet_outlined, activeIcon: Icons.account_balance_wallet, route: Routes.fees),
  TabItem(label: 'More', icon: Icons.menu, activeIcon: Icons.menu, route: Routes.more),
];

const _teacherTabs = <TabItem>[
  TabItem(label: 'Dashboard', icon: Icons.grid_view_outlined, activeIcon: Icons.grid_view, route: Routes.dashboard),
  TabItem(label: 'Attendance', icon: Icons.check_box_outlined, activeIcon: Icons.check_box, route: Routes.attendance),
  TabItem(label: 'Homework', icon: Icons.description_outlined, activeIcon: Icons.description, route: Routes.homework),
  TabItem(label: 'Timetable', icon: Icons.calendar_today_outlined, activeIcon: Icons.calendar_today, route: Routes.timetable),
  TabItem(label: 'More', icon: Icons.menu, activeIcon: Icons.menu, route: Routes.more),
];

const _parentTabs = <TabItem>[
  TabItem(label: 'Home', icon: Icons.home_outlined, activeIcon: Icons.home, route: Routes.dashboard),
  TabItem(label: 'Fees', icon: Icons.account_balance_wallet_outlined, activeIcon: Icons.account_balance_wallet, route: Routes.fees),
  TabItem(label: 'Attendance', icon: Icons.check_box_outlined, activeIcon: Icons.check_box, route: Routes.attendance),
  TabItem(label: 'Notices', icon: Icons.campaign_outlined, activeIcon: Icons.campaign, route: Routes.announcements),
  TabItem(label: 'More', icon: Icons.menu, activeIcon: Icons.menu, route: Routes.more),
];

const _studentTabs = <TabItem>[
  TabItem(label: 'Home', icon: Icons.home_outlined, activeIcon: Icons.home, route: Routes.dashboard),
  TabItem(label: 'Timetable', icon: Icons.calendar_today_outlined, activeIcon: Icons.calendar_today, route: Routes.timetable),
  TabItem(label: 'Homework', icon: Icons.description_outlined, activeIcon: Icons.description, route: Routes.homework),
  TabItem(label: 'Exams', icon: Icons.emoji_events_outlined, activeIcon: Icons.emoji_events, route: Routes.exams),
  TabItem(label: 'More', icon: Icons.menu, activeIcon: Icons.menu, route: Routes.more),
];

List<TabItem> tabsForRole(AppRole? role) {
  switch (role) {
    case AppRole.superAdmin:
    case AppRole.admin:
      return _adminTabs;
    case AppRole.teacher:
    case AppRole.staff:
      return _teacherTabs;
    case AppRole.parent:
      return _parentTabs;
    case AppRole.student:
      return _studentTabs;
    case null:
      return _adminTabs;
  }
}

// ─── "More" menu module registry (permission + role gated) ──────────────────

const moreMenuModules = <ModuleEntry>[
  ModuleEntry(title: 'Students', icon: Icons.people_outline, route: Routes.students, permission: 'students:view', roles: [AppRole.admin, AppRole.superAdmin, AppRole.teacher]),
  ModuleEntry(title: 'Staff', icon: Icons.badge_outlined, route: Routes.staff, permission: 'staff:view', roles: [AppRole.admin, AppRole.superAdmin]),
  ModuleEntry(title: 'Attendance', icon: Icons.check_box_outlined, route: Routes.attendance),
  ModuleEntry(title: 'Homework', icon: Icons.description_outlined, route: Routes.homework),
  ModuleEntry(title: 'Timetable', icon: Icons.calendar_today_outlined, route: Routes.timetable),
  ModuleEntry(title: 'Exams', icon: Icons.emoji_events_outlined, route: Routes.exams),
  ModuleEntry(title: 'Fees', icon: Icons.account_balance_wallet_outlined, route: Routes.fees),
  ModuleEntry(title: 'Announcements', icon: Icons.campaign_outlined, route: Routes.announcements),
  ModuleEntry(title: 'Leaves', icon: Icons.event_busy_outlined, route: Routes.leaves),
  ModuleEntry(title: 'PTM', icon: Icons.groups_outlined, route: Routes.ptm, roles: [AppRole.parent, AppRole.teacher, AppRole.admin, AppRole.superAdmin]),
  ModuleEntry(title: 'Expenses', icon: Icons.shopping_bag_outlined, route: Routes.expenses, roles: [AppRole.parent, AppRole.student]),
  ModuleEntry(title: 'Calendar', icon: Icons.calendar_month_outlined, route: Routes.calendar),
  ModuleEntry(title: 'Library', icon: Icons.menu_book_outlined, route: Routes.library, roles: [AppRole.admin, AppRole.superAdmin, AppRole.teacher]),
  ModuleEntry(title: 'Transport', icon: Icons.directions_bus_outlined, route: Routes.transport, roles: [AppRole.admin, AppRole.superAdmin]),
  ModuleEntry(title: 'Reports', icon: Icons.bar_chart_outlined, route: Routes.reports, roles: [AppRole.admin, AppRole.superAdmin]),
  ModuleEntry(title: 'Settings', icon: Icons.settings_outlined, route: Routes.settings),
];
