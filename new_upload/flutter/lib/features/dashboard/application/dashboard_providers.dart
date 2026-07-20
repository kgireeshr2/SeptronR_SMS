import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/domain/app_role.dart';
import '../data/dashboard_repository.dart';

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  return DashboardRepository(ref.watch(dioProvider));
});

final dashboardProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) {
  final role = ref.watch(roleProvider) ?? AppRole.admin;
  return ref.watch(dashboardRepositoryProvider).fetch(role);
});
