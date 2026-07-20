import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../academic/application/academic_providers.dart';
import '../data/timetable_repository.dart';
import '../domain/timetable_slot.dart';

final timetableRepositoryProvider = Provider<TimetableRepository>((ref) {
  return TimetableRepository(ref.watch(dioProvider));
});

/// Timetable for a section in the current academic year.
final sectionTimetableProvider = FutureProvider.family
    .autoDispose<List<TimetableSlot>, String>((ref, sectionId) async {
  final year = await ref.watch(currentYearProvider.future);
  if (year == null) return [];
  return ref.watch(timetableRepositoryProvider).bySection(sectionId, year.id);
});
