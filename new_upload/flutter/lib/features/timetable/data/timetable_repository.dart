import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/timetable_slot.dart';

class TimetableRepository {
  TimetableRepository(this._dio);
  final Dio _dio;

  /// `GET /timetable/section/{section_id}?academic_year_id=` → grid.
  Future<List<TimetableSlot>> bySection(
      String sectionId, String academicYearId) async {
    return _fetch('/timetable/section/$sectionId', academicYearId);
  }

  /// `GET /timetable/teacher/{teacher_id}?academic_year_id=` → schedule.
  Future<List<TimetableSlot>> byTeacher(
      String teacherId, String academicYearId) async {
    return _fetch('/timetable/teacher/$teacherId', academicYearId);
  }

  Future<List<TimetableSlot>> _fetch(String path, String academicYearId) async {
    try {
      final res = await _dio
          .get(path, queryParameters: {'academic_year_id': academicYearId});
      return _parseGrid(res.data);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// The grid may be a flat list of slots, or a map keyed by day → [slots].
  List<TimetableSlot> _parseGrid(dynamic data) {
    final out = <TimetableSlot>[];
    if (data is List) {
      for (final e in data.whereType<Map>()) {
        out.add(TimetableSlot.fromJson(Map<String, dynamic>.from(e)));
      }
    } else if (data is Map) {
      // Either {entries:[...]} or {Monday:[...], Tuesday:[...]}.
      final entries = data['entries'] ?? data['slots'];
      if (entries is List) {
        for (final e in entries.whereType<Map>()) {
          out.add(TimetableSlot.fromJson(Map<String, dynamic>.from(e)));
        }
      } else {
        data.forEach((day, slots) {
          if (slots is List) {
            for (final e in slots.whereType<Map>()) {
              final m = Map<String, dynamic>.from(e);
              m.putIfAbsent('day_name', () => day.toString());
              out.add(TimetableSlot.fromJson(m));
            }
          }
        });
      }
    }
    return out;
  }
}
