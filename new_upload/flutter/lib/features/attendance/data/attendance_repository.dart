import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/attendance.dart';

class AttendanceRepository {
  AttendanceRepository(this._dio);
  final Dio _dio;

  static String _ymd(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  /// Mark section attendance — `POST /attendance/section/{section_id}`.
  /// Body: { section_id, academic_year_id, date, session_type, entries:[{student_id,status,remarks}] }.
  Future<void> markSection({
    required String sectionId,
    required String academicYearId,
    required DateTime date,
    required Map<String, String> statuses,
    String sessionType = 'full_day',
  }) async {
    try {
      await _dio.post('/attendance/section/$sectionId', data: {
        'section_id': sectionId,
        'academic_year_id': academicYearId,
        'date': _ymd(date),
        'session_type': sessionType,
        'entries': [
          for (final e in statuses.entries)
            {'student_id': e.key, 'status': e.value},
        ],
      });
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Existing marks for a section/date → {student_id: status} for prefill.
  /// `GET /attendance/section/{section_id}?date=&session=`.
  Future<Map<String, String>> sectionStatuses({
    required String sectionId,
    required DateTime date,
    String session = 'full_day',
  }) async {
    try {
      final res = await _dio.get(
        '/attendance/section/$sectionId',
        queryParameters: {'date': _ymd(date), 'session': session},
      );
      final data = res.data;
      final entries = (data is Map ? data['entries'] : null);
      final map = <String, String>{};
      if (entries is List) {
        for (final r in entries.whereType<Map>()) {
          final id = r['student_id']?.toString();
          final st = (r['status'] is Map)
              ? r['status']['value']?.toString()
              : r['status']?.toString();
          if (id != null && st != null) map[id] = st;
        }
      }
      return map;
    } catch (_) {
      return {};
    }
  }

  /// Per-student attendance summary over a date range.
  /// `GET /attendance/student/{student_id}?from=&to=`.
  Future<AttendanceSummary> studentSummary({
    required String studentId,
    required DateTime from,
    required DateTime to,
  }) async {
    try {
      final res = await _dio.get(
        '/attendance/student/$studentId',
        queryParameters: {'from': _ymd(from), 'to': _ymd(to)},
      );
      return AttendanceSummary.fromJson(
          Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
