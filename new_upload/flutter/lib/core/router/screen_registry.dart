import 'package:flutter/material.dart';

import '../../features/announcements/presentation/announcements_screen.dart';
import '../../features/attendance/presentation/attendance_screen.dart';
import '../../features/calendar/presentation/calendar_screen.dart';
import '../../features/dashboard/presentation/dashboard_screen.dart';
import '../../features/exams/presentation/exams_screen.dart';
import '../../features/fees/presentation/fees_screen.dart';
import '../../features/homework/presentation/homework_screen.dart';
import '../../features/leaves/presentation/leaves_screen.dart';
import '../../features/library/presentation/library_screen.dart';
import '../../features/more/presentation/more_screen.dart';
import '../../features/personal_expenses/presentation/personal_expenses_screen.dart';
import '../../features/ptm/presentation/ptm_screen.dart';
import '../../features/reports/presentation/reports_screen.dart';
import '../../features/settings/presentation/settings_screen.dart';
import '../../features/staff/presentation/staff_screen.dart';
import '../../features/students/presentation/students_screen.dart';
import '../../features/timetable/presentation/timetable_screen.dart';
import '../../features/transport/presentation/transport_screen.dart';
import '../../shared/widgets/placeholder_screen.dart';
import 'routes.dart';

/// Single source of truth mapping a feature route to its screen widget.
/// Used both by the [AppShell] (tab bodies) and the router (pushed routes).
/// Screens not yet implemented fall back to [PlaceholderScreen].
Widget screenForRoute(String route) {
  switch (route) {
    case Routes.dashboard:
      return const DashboardScreen();
    case Routes.attendance:
      return const AttendanceScreen();
    case Routes.homework:
      return const HomeworkScreen();
    case Routes.fees:
      return const FeesScreen();
    case Routes.announcements:
      return const AnnouncementsScreen();
    case Routes.students:
      return const StudentsScreen();
    case Routes.staff:
      return const StaffScreen();
    case Routes.timetable:
      return const TimetableScreen();
    case Routes.exams:
      return const ExamsScreen();
    case Routes.leaves:
      return const LeavesScreen();
    case Routes.calendar:
      return const CalendarScreen();
    case Routes.ptm:
      return const PtmScreen();
    case Routes.expenses:
      return const PersonalExpensesScreen();
    case Routes.more:
      return const MoreScreen();
    case Routes.settings:
      return const SettingsScreen();

    case Routes.library:
      return const LibraryScreen();
    case Routes.transport:
      return const TransportScreen();
    case Routes.reports:
      return const ReportsScreen();
    default:
      return const PlaceholderScreen(title: 'Coming soon');
  }
}
