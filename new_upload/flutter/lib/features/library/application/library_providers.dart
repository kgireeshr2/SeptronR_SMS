import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/library_repository.dart';
import '../domain/library_models.dart';

final libraryRepositoryProvider = Provider<LibraryRepository>((ref) {
  return LibraryRepository(ref.watch(dioProvider));
});

final bookSearchProvider =
    FutureProvider.family.autoDispose<List<Book>, String>((ref, query) {
  return ref.watch(libraryRepositoryProvider).searchBooks(query);
});

final bookIssuesProvider =
    FutureProvider.autoDispose<List<BookIssue>>((ref) {
  return ref.watch(libraryRepositoryProvider).issues();
});
