import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/library_models.dart';

class LibraryRepository {
  LibraryRepository(this._dio);
  final Dio _dio;

  Future<List<Book>> searchBooks(String query) async {
    try {
      final res = await _dio.get('/library/books', queryParameters: {
        if (query.isNotEmpty) 'search': query,
        'page': 1,
        'page_size': 100,
      });
      return Paginated.fromJson(res.data, Book.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// `GET /library/issues` — current issues (admin/librarian view).
  Future<List<BookIssue>> issues({bool overdueOnly = false}) async {
    try {
      final res = await _dio.get('/library/issues',
          queryParameters: {if (overdueOnly) 'overdue': true});
      return Paginated.fromJson(res.data, BookIssue.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
