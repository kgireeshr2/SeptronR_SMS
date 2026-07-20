import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/academic_repository.dart';
import '../domain/academic_year.dart';

final academicRepositoryProvider = Provider<AcademicRepository>((ref) {
  return AcademicRepository(ref.watch(dioProvider));
});

final academicYearsProvider =
    FutureProvider<List<AcademicYear>>((ref) {
  return ref.watch(academicRepositoryProvider).years();
});

/// The current academic year (flagged `is_current`, else the first one).
/// Null if the user lacks permission or none exist.
final currentYearProvider = FutureProvider<AcademicYear?>((ref) async {
  final years = await ref.watch(academicYearsProvider.future);
  if (years.isEmpty) return null;
  return years.firstWhere((y) => y.isCurrent, orElse: () => years.first);
});

/// Classes (with nested sections) for the current academic year.
final classesProvider = FutureProvider<List<ClassRoom>>((ref) async {
  final year = await ref.watch(currentYearProvider.future);
  if (year == null) return [];
  return ref.watch(academicRepositoryProvider).classes(year.id);
});
