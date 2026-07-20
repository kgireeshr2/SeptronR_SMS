import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/exam.dart';

class ExamsRepository {
  ExamsRepository(this._dio);
  final Dio _dio;

  Future<List<Exam>> list() async {
    try {
      final res = await _dio.get('/exams');
      return Paginated.fromJson(res.data, Exam.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// `GET /exams/{exam_id}/marks` → marks for every student in the exam.
  Future<List<ExamMark>> marks(String examId) async {
    try {
      final res = await _dio.get('/exams/$examId/marks');
      return Paginated.fromJson(res.data, ExamMark.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// `POST /exams/{exam_id}/marks` with `{ entries: [{student_id, marks_obtained, is_absent}] }`.
  Future<void> enterMarks(
      String examId, List<Map<String, dynamic>> entries) async {
    try {
      await _dio.post('/exams/$examId/marks', data: {'entries': entries});
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// API path for a student's report card PDF (used by [FileDownloader]).
  String reportCardPath(String examId, String studentId) =>
      '/exams/$examId/report-card/$studentId/pdf';
}
