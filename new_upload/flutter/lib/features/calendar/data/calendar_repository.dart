import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/calendar_event.dart';

class CalendarRepository {
  CalendarRepository(this._dio);
  final Dio _dio;

  static String _ymd(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  /// Events + holidays within [start, end], merged and date-sorted.
  Future<List<CalendarEvent>> agenda(DateTime start, DateTime end) async {
    final events = <CalendarEvent>[];

    try {
      final res = await _dio.get('/calendar',
          queryParameters: {'start': _ymd(start), 'end': _ymd(end)});
      events.addAll(_parse(res.data, isHoliday: false));
    } on DioException catch (e) {
      if (e.response?.statusCode != 404) {
        throw ApiException.fromDio(e);
      }
    }

    try {
      final res = await _dio.get('/holidays');
      events.addAll(_parse(res.data, isHoliday: true)
          .where((h) =>
              h.date == null ||
              (!h.date!.isBefore(start) && !h.date!.isAfter(end))));
    } catch (_) {
      // Holidays optional.
    }

    events.sort((a, b) =>
        (a.date ?? DateTime(2100)).compareTo(b.date ?? DateTime(2100)));
    return events;
  }

  /// `POST /calendar` — create an event (calendar:write).
  Future<void> createEvent({
    required String title,
    required DateTime date,
    String eventType = 'other',
    String? description,
  }) async {
    final start = DateTime(date.year, date.month, date.day, 0, 0);
    final end = DateTime(date.year, date.month, date.day, 23, 59);
    try {
      await _dio.post('/calendar', data: {
        'title': title,
        'event_type': eventType,
        'start_datetime': start.toIso8601String(),
        'end_datetime': end.toIso8601String(),
        'all_day': true,
        'audience': 'all',
        if (description != null) 'description': description,
      });
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  List<CalendarEvent> _parse(dynamic data, {required bool isHoliday}) {
    final list = data is List
        ? data
        : (data is Map ? (data['items'] ?? data['events'] ?? data['data']) : null);
    if (list is! List) return [];
    return list
        .whereType<Map>()
        .map((e) => CalendarEvent.fromJson(Map<String, dynamic>.from(e),
            isHoliday: isHoliday))
        .toList();
  }
}
