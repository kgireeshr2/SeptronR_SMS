import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/leaves_repository.dart';
import '../domain/leave.dart';

final leavesRepositoryProvider = Provider<LeavesRepository>((ref) {
  return LeavesRepository(ref.watch(dioProvider));
});

final myLeavesProvider =
    FutureProvider.autoDispose<List<LeaveApplication>>((ref) {
  return ref.watch(leavesRepositoryProvider).myLeaves();
});

final pendingLeavesProvider =
    FutureProvider.autoDispose<List<LeaveApplication>>((ref) {
  return ref.watch(leavesRepositoryProvider).list(status: 'pending');
});

final leaveTypesProvider =
    FutureProvider.autoDispose<List<LeaveType>>((ref) {
  return ref.watch(leavesRepositoryProvider).types();
});

final myLeaveBalancesProvider =
    FutureProvider.autoDispose<List<LeaveBalance>>((ref) {
  return ref.watch(leavesRepositoryProvider).myBalances();
});
