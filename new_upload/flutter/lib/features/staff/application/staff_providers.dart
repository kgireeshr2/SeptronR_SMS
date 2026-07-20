import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/staff_repository.dart';
import '../domain/staff_member.dart';

final staffRepositoryProvider = Provider<StaffRepository>((ref) {
  return StaffRepository(ref.watch(dioProvider));
});

final staffListProvider =
    FutureProvider.family.autoDispose<List<StaffMember>, String>((ref, search) {
  return ref.watch(staffRepositoryProvider).list(search: search);
});
