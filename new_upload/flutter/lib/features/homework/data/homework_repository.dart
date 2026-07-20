import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/homework.dart';

class HomeworkRepository {
  HomeworkRepository(this._dio);
  final Dio _dio;

  Future<List<Homework>> list({String? classId, String? subjectId}) async {
    try {
      final res = await _dio.get('/homework', queryParameters: {
        'page': 1,
        'page_size': 100,
        if (classId != null) 'class_id': classId,
        if (subjectId != null) 'subject_id': subjectId,
      });
      return Paginated.fromJson(res.data, Homework.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<Homework> create({
    required String title,
    String? description,
    String? subjectId,
    String? classId,
    DateTime? dueDate,
  }) async {
    try {
      final res = await _dio.post('/homework', data: {
        'title': title,
        if (description != null) 'description': description,
        if (subjectId != null) 'subject_id': subjectId,
        if (classId != null) 'class_id': classId,
        if (dueDate != null)
          'due_date': dueDate.toIso8601String().split('T').first,
      });
      return Homework.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<void> delete(String id) async {
    try {
      await _dio.delete('/homework/$id');
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<HomeworkSubmission>> submissions(String homeworkId) async {
    try {
      final res = await _dio.get('/homework/$homeworkId/submissions');
      return Paginated.fromJson(res.data, HomeworkSubmission.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Student submits homework — needs the student's own id.
  Future<void> submit({
    required String homeworkId,
    required String studentId,
    String? content,
  }) async {
    try {
      await _dio.post('/homework/$homeworkId/submissions', data: {
        'homework_id': homeworkId,
        'student_id': studentId,
        if (content != null) 'content': content,
      });
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// Teacher grades a submission — `PUT /homework/submissions/{sub_id}/grade`.
  Future<void> grade(String submissionId,
      {int? marks, String? remarks}) async {
    try {
      await _dio.put('/homework/submissions/$submissionId/grade', data: {
        if (marks != null) 'marks_given': marks,
        if (remarks != null) 'remarks': remarks,
      });
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
