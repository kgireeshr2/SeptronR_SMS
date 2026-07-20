import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/exams_repository.dart';
import '../domain/exam.dart';

final examsRepositoryProvider = Provider<ExamsRepository>((ref) {
  return ExamsRepository(ref.watch(dioProvider));
});

final examsListProvider = FutureProvider.autoDispose<List<Exam>>((ref) {
  return ref.watch(examsRepositoryProvider).list();
});

final examMarksProvider =
    FutureProvider.family.autoDispose<List<ExamMark>, String>((ref, examId) {
  return ref.watch(examsRepositoryProvider).marks(examId);
});
