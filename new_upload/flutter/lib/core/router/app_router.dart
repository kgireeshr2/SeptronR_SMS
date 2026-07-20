import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/application/auth_controller.dart';
import '../../features/auth/application/auth_state.dart';
import '../../features/auth/presentation/change_password_screen.dart';
import '../../features/auth/presentation/forgot_password_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/otp_screen.dart';
import '../../features/shell/app_shell.dart';
import '../../features/shell/splash_screen.dart';
import 'routes.dart';
import 'screen_registry.dart';

/// Module routes that can be pushed (from the More menu or in-app links).
const _moduleRoutes = <String>[
  Routes.dashboard,
  Routes.students,
  Routes.staff,
  Routes.attendance,
  Routes.homework,
  Routes.fees,
  Routes.timetable,
  Routes.exams,
  Routes.announcements,
  Routes.leaves,
  Routes.calendar,
  Routes.library,
  Routes.transport,
  Routes.reports,
  Routes.settings,
  Routes.ptm,
  Routes.expenses,
];

final routerProvider = Provider<GoRouter>((ref) {
  // Bridge: re-evaluate redirects whenever auth status flips.
  final refresh = ValueNotifier<int>(0);
  ref.listen<AuthStatus>(
    authControllerProvider.select((s) => s.status),
    (_, __) => refresh.value++,
  );
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: refresh,
    redirect: (context, state) {
      final status = ref.read(authControllerProvider).status;
      final loc = state.matchedLocation;

      const authLocations = {
        Routes.login,
        Routes.otp,
        Routes.forgotPassword,
      };

      // Still restoring the session → stay on splash.
      if (status == AuthStatus.unknown) {
        return loc == '/' ? null : '/';
      }

      final authed = status == AuthStatus.authenticated;
      final onAuthScreen = authLocations.contains(loc) || loc == '/';

      if (!authed) {
        return onAuthScreen && loc != '/' ? null : Routes.login;
      }
      // Authenticated but sitting on splash/auth → go home.
      if (authed && onAuthScreen) return Routes.app;
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, __) => const SplashScreen()),
      GoRoute(path: Routes.login, builder: (_, __) => const LoginScreen()),
      GoRoute(path: Routes.otp, builder: (_, __) => const OtpScreen()),
      GoRoute(
        path: Routes.forgotPassword,
        builder: (_, __) => const ForgotPasswordScreen(),
      ),
      GoRoute(path: Routes.app, builder: (_, __) => const AppShell()),
      GoRoute(
        path: Routes.changePassword,
        builder: (_, __) => const ChangePasswordScreen(),
      ),
      // Module routes (pushed from the More menu). Each renders its screen.
      for (final r in _moduleRoutes)
        GoRoute(path: r, builder: (_, __) => screenForRoute(r)),
    ],
  );
});
