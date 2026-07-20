import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../auth/domain/app_role.dart';

class DashboardRepository {
  DashboardRepository(this._dio);
  final Dio _dio;

  /// Fetches the role-appropriate dashboard payload. Returns a raw map; the
  /// UI reads keys defensively since shapes differ per role.
  Future<Map<String, dynamic>> fetch(AppRole role) async {
    final path = switch (role) {
      AppRole.superAdmin || AppRole.admin => '/dashboard/admin',
      AppRole.teacher || AppRole.staff => '/dashboard/teacher',
      AppRole.parent => '/dashboard/parent',
      AppRole.student => '/dashboard/student',
    };
    try {
      final res = await _dio.get(path);
      final data = res.data;
      return data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
