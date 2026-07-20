import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../profile/application/identity_providers.dart';
import '../data/transport_repository.dart';
import '../domain/transport_models.dart';

final transportRepositoryProvider = Provider<TransportRepository>((ref) {
  return TransportRepository(ref.watch(dioProvider));
});

/// Transport assignment for the resolved student (parent's active child).
final myTransportProvider =
    FutureProvider.autoDispose<TransportRoute?>((ref) async {
  final studentId = ref.watch(currentStudentIdProvider);
  if (studentId == null) return null;
  return ref.watch(transportRepositoryProvider).studentTransport(studentId);
});

final routesProvider =
    FutureProvider.autoDispose<List<TransportRoute>>((ref) {
  return ref.watch(transportRepositoryProvider).routes();
});

final vehiclesProvider = FutureProvider.autoDispose<List<Vehicle>>((ref) {
  return ref.watch(transportRepositoryProvider).vehicles();
});
