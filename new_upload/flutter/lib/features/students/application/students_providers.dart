import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/students_repository.dart';
import '../domain/student.dart';

final studentsRepositoryProvider = Provider<StudentsRepository>((ref) {
  return StudentsRepository(ref.watch(dioProvider));
});

/// Filter args for a student list query.
class StudentQuery {
  const StudentQuery({this.classId, this.sectionId, this.search});
  final String? classId;
  final String? sectionId;
  final String? search;

  @override
  bool operator ==(Object other) =>
      other is StudentQuery &&
      other.classId == classId &&
      other.sectionId == sectionId &&
      other.search == search;

  @override
  int get hashCode => Object.hash(classId, sectionId, search);
}

final studentsProvider =
    FutureProvider.family<List<Student>, StudentQuery>((ref, q) {
  return ref.watch(studentsRepositoryProvider).list(
        classId: q.classId,
        sectionId: q.sectionId,
        search: q.search,
      );
});
