import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../profile/application/identity_providers.dart';
import '../data/fees_repository.dart';
import '../domain/fee_invoice.dart';

final feesRepositoryProvider = Provider<FeesRepository>((ref) {
  return FeesRepository(ref.watch(dioProvider));
});

/// Parent/student: fee statement for the resolved student. Null if unresolved.
final feeStatementProvider =
    FutureProvider.autoDispose<FeeStatement?>((ref) async {
  final studentId = ref.watch(currentStudentIdProvider);
  if (studentId == null) return null;
  return ref.watch(feesRepositoryProvider).studentStatement(studentId);
});

/// Admin: all invoices.
final adminInvoicesProvider =
    FutureProvider.autoDispose<List<FeeInvoice>>((ref) {
  return ref.watch(feesRepositoryProvider).invoices();
});

final monthlyCollectionProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) {
  return ref.watch(feesRepositoryProvider).monthlyCollection();
});

final defaultersProvider =
    FutureProvider.autoDispose<List<Defaulter>>((ref) {
  return ref.watch(feesRepositoryProvider).defaulters();
});
