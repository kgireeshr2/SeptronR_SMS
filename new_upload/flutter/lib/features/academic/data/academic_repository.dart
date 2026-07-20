import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/academic_year.dart';

class AcademicRepository {
  AcademicRepository(this._dio);
  final Dio _dio;

  Future<List<AcademicYear>> years() async {
    try {
      final res = await _dio.get('/academic-years');
      return Paginated.fromJson(res.data, AcademicYear.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<ClassRoom>> classes(String academicYearId) async {
    try {
      final res = await _dio.get('/classes',
          queryParameters: {'academic_year_id': academicYearId});
      return Paginated.fromJson(res.data, ClassRoom.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
