import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/homework_repository.dart';
import '../domain/homework.dart';

final homeworkRepositoryProvider = Provider<HomeworkRepository>((ref) {
  return HomeworkRepository(ref.watch(dioProvider));
});

final homeworkListProvider =
    FutureProvider.autoDispose<List<Homework>>((ref) {
  return ref.watch(homeworkRepositoryProvider).list();
});

final homeworkSubmissionsProvider = FutureProvider.family
    .autoDispose<List<HomeworkSubmission>, String>((ref, homeworkId) {
  return ref.watch(homeworkRepositoryProvider).submissions(homeworkId);
});
