import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/calendar_repository.dart';
import '../domain/calendar_event.dart';

final calendarRepositoryProvider = Provider<CalendarRepository>((ref) {
  return CalendarRepository(ref.watch(dioProvider));
});

/// Month key as (year, month) so the provider re-runs when the month changes.
class MonthKey {
  const MonthKey(this.year, this.month);
  final int year;
  final int month;

  DateTime get start => DateTime(year, month, 1);
  DateTime get end => DateTime(year, month + 1, 0);

  @override
  bool operator ==(Object other) =>
      other is MonthKey && other.year == year && other.month == month;

  @override
  int get hashCode => Object.hash(year, month);
}

final agendaProvider = FutureProvider.family
    .autoDispose<List<CalendarEvent>, MonthKey>((ref, key) {
  return ref.watch(calendarRepositoryProvider).agenda(key.start, key.end);
});
