import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/staff_member.dart';

class StaffRepository {
  StaffRepository(this._dio);
  final Dio _dio;

  Future<List<StaffMember>> list({String? search}) async {
    try {
      final res = await _dio.get('/staff', queryParameters: {
        'page': 1,
        'page_size': 100,
        if (search != null && search.isNotEmpty) 'search': search,
      });
      return Paginated.fromJson(res.data, StaffMember.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<StaffMember> get(String id) async {
    try {
      final res = await _dio.get('/staff/$id');
      return StaffMember.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
