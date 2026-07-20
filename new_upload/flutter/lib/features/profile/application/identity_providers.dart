import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/domain/app_role.dart';
import '../../dashboard/application/dashboard_providers.dart';
import '../domain/child_ref.dart';

const _kActiveChildKey = 'sms_active_child_id';

/// Children linked to the logged-in parent (from `GET /dashboard/parent`).
/// Empty for non-parent roles.
final childrenProvider = FutureProvider<List<ChildRef>>((ref) async {
  final role = ref.watch(roleProvider);
  if (role != AppRole.parent) return const [];
  final data = await ref.watch(dashboardRepositoryProvider).fetch(AppRole.parent);
  final raw = data['children'];
  if (raw is! List) return const [];
  return raw
      .whereType<Map>()
      .map((e) => ChildRef.fromJson(Map<String, dynamic>.from(e)))
      .toList();
});

/// Selected child id (persisted). Parents with multiple children switch this.
class ActiveChildController extends Notifier<String?> {
  @override
  String? build() {
    _restore();
    return null;
  }

  Future<void> _restore() async {
    final stored = await ref.read(secureStorageProvider).read(_kActiveChildKey);
    if (stored != null && stored.isNotEmpty) state = stored;
  }

  Future<void> select(String childId) async {
    state = childId;
    await ref.read(secureStorageProvider).write(_kActiveChildKey, childId);
  }
}

final activeChildIdProvider =
    NotifierProvider<ActiveChildController, String?>(ActiveChildController.new);

/// The resolved active child: the selected one, else the first child.
final activeChildProvider = Provider<ChildRef?>((ref) {
  final children = ref.watch(childrenProvider).valueOrNull ?? const [];
  if (children.isEmpty) return null;
  final id = ref.watch(activeChildIdProvider);
  return children.firstWhere(
    (c) => c.id == id,
    orElse: () => children.first,
  );
});

/// The logged-in student's own record, resolved via `GET /students/me`
/// (only for the student role). Cached for the session.
final studentSelfProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  final role = ref.watch(roleProvider);
  if (role != AppRole.student) return null;
  try {
    final res = await ref.watch(dioProvider).get('/students/me');
    final data = res.data;
    return data is Map ? Map<String, dynamic>.from(data) : null;
  } catch (_) {
    return null; // no linked student record → screens degrade gracefully
  }
});

/// The student_id to use for self-service reads.
/// - Parent → active child id.
/// - Student → own student id resolved from `/students/me`.
final currentStudentIdProvider = Provider<String?>((ref) {
  final role = ref.watch(roleProvider);
  if (role == AppRole.parent) return ref.watch(activeChildProvider)?.id;
  if (role == AppRole.student) {
    return ref.watch(studentSelfProvider).valueOrNull?['id']?.toString();
  }
  return null;
});

/// The logged-in student's own current section id (for timetable, etc.).
final currentStudentSectionIdProvider = Provider<String?>((ref) {
  final role = ref.watch(roleProvider);
  if (role == AppRole.student) {
    return ref.watch(studentSelfProvider).valueOrNull?['section_id']?.toString();
  }
  return null;
});
