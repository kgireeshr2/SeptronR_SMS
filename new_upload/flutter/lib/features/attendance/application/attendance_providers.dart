import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/attendance_repository.dart';
import '../domain/attendance.dart';

final attendanceRepositoryProvider = Provider<AttendanceRepository>((ref) {
  return AttendanceRepository(ref.watch(dioProvider));
});

/// Args for a per-student monthly summary query.
class StudentMonthKey {
  const StudentMonthKey({
    required this.studentId,
    required this.from,
    required this.to,
  });
  final String studentId;
  final DateTime from;
  final DateTime to;

  @override
  bool operator ==(Object other) =>
      other is StudentMonthKey &&
      other.studentId == studentId &&
      other.from == from &&
      other.to == to;

  @override
  int get hashCode => Object.hash(studentId, from, to);
}

final studentAttendanceProvider = FutureProvider.family
    .autoDispose<AttendanceSummary, StudentMonthKey>((ref, key) {
  return ref.watch(attendanceRepositoryProvider).studentSummary(
        studentId: key.studentId,
        from: key.from,
        to: key.to,
      );
});
