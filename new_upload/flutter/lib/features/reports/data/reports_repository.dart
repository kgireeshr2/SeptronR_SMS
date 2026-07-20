import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';

class ReportInfo {
  const ReportInfo({required this.id, required this.group});
  final String id;
  final String group;

  /// "student_attendance" → "Student Attendance".
  String get title => id
      .split('_')
      .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
      .join(' ');
}

class ReportsRepository {
  ReportsRepository(this._dio);
  final Dio _dio;

  Future<List<ReportInfo>> available() async {
    try {
      final res = await _dio.get('/reports/available');
      final data = res.data;
      final out = <ReportInfo>[];
      if (data is Map) {
        data.forEach((group, ids) {
          if (ids is List) {
            for (final id in ids) {
              out.add(ReportInfo(id: id.toString(), group: group.toString()));
            }
          }
        });
      }
      return out;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Returns report rows (list of column→value maps).
  Future<List<Map<String, dynamic>>> run(
    String reportId, {
    String? yearId,
    Map<String, dynamic> filters = const {},
  }) async {
    try {
      final res = await _dio.get('/reports/$reportId', queryParameters: {
        if (yearId != null) 'year_id': yearId,
        ...filters,
      });
      final data = res.data;
      final rows = (data is Map) ? (data['data'] ?? data['rows']) : data;
      if (rows is List) {
        return rows
            .whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
      }
      return const [];
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
