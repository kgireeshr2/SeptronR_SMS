import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/student.dart';

class StudentsRepository {
  StudentsRepository(this._dio);
  final Dio _dio;

  Future<List<Student>> list({
    String? classId,
    String? sectionId,
    String? search,
    int page = 1,
    int pageSize = 50,
  }) async {
    try {
      final res = await _dio.get('/students', queryParameters: {
        'page': page,
        'page_size': pageSize,
        if (classId != null) 'class_id': classId,
        if (sectionId != null) 'section_id': sectionId,
        if (search != null && search.isNotEmpty) 'search': search,
      });
      return Paginated.fromJson(res.data, Student.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<Student> get(String id) async {
    try {
      final res = await _dio.get('/students/$id');
      return Student.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
