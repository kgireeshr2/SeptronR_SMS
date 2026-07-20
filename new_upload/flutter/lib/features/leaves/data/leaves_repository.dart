import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/leave.dart';

class LeavesRepository {
  LeavesRepository(this._dio);
  final Dio _dio;

  static String _ymd(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Future<List<LeaveApplication>> myLeaves() async {
    try {
      final res = await _dio.get('/leaves/applications/my');
      return Paginated.fromJson(res.data, LeaveApplication.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<LeaveApplication>> list({String? status}) async {
    try {
      final res = await _dio.get('/leaves/applications',
          queryParameters: {if (status != null) 'status': status});
      return Paginated.fromJson(res.data, LeaveApplication.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<LeaveType>> types() async {
    try {
      final res = await _dio.get('/leaves/types');
      return Paginated.fromJson(res.data, LeaveType.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<LeaveBalance>> myBalances() async {
    try {
      final res = await _dio.get('/leaves/balances/my');
      return Paginated.fromJson(res.data, LeaveBalance.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<void> apply({
    required String leaveTypeId,
    required DateTime from,
    required DateTime to,
    required double totalDays,
    String? reason,
  }) async {
    try {
      await _dio.post('/leaves/applications', data: {
        'leave_type_id': leaveTypeId,
        'from_date': _ymd(from),
        'to_date': _ymd(to),
        'total_days': totalDays,
        if (reason != null) 'reason': reason,
      });
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<void> cancel(String id) =>
      _patch('/leaves/applications/$id/cancel');

  /// Approve or reject — `PATCH /leaves/applications/{id}/review` { status, remarks }.
  Future<void> review(String id,
          {required bool approved, String? remarks}) =>
      _patch('/leaves/applications/$id/review', {
        'status': approved ? 'approved' : 'rejected',
        if (remarks != null) 'remarks': remarks,
      });

  Future<void> _patch(String path, [Map<String, dynamic>? body]) async {
    try {
      await _dio.patch(path, data: body);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
