import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/fee_invoice.dart';

class FeesRepository {
  FeesRepository(this._dio);
  final Dio _dio;

  /// Parent/student: full statement for a student (totals + invoices).
  /// `GET /fees/students/{student_id}/statement`.
  Future<FeeStatement> studentStatement(String studentId) async {
    try {
      final res = await _dio.get('/fees/students/$studentId/statement');
      return FeeStatement.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Admin: all invoices, optionally filtered by status.
  Future<List<FeeInvoice>> invoices({String? status}) async {
    try {
      final res = await _dio.get('/fees/invoices', queryParameters: {
        if (status != null) 'status': status,
      });
      return Paginated.fromJson(res.data, FeeInvoice.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Admin: monthly collection summary (raw map — shape varies).
  Future<Map<String, dynamic>> monthlyCollection({int? month, int? year}) async {
    try {
      final res = await _dio.get('/fees/reports/monthly-collection',
          queryParameters: {
            if (month != null) 'month': month,
            if (year != null) 'year': year,
          });
      final data = res.data;
      return data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Admin: fee defaulters.
  Future<List<Defaulter>> defaulters() async {
    try {
      final res = await _dio.get('/fees/reports/defaulters');
      return Paginated.fromJson(res.data, Defaulter.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
