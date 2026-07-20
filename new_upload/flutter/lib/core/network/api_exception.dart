import 'package:dio/dio.dart';

/// Normalized API error with a user-presentable message.
class ApiException implements Exception {
  ApiException(this.message, {this.statusCode, this.data});

  final String message;
  final int? statusCode;
  final dynamic data;

  @override
  String toString() => message;

  /// Extracts the backend `message`/`detail` from a DioException, falling back
  /// to a sensible default per status code.
  factory ApiException.fromDio(DioException e) {
    final res = e.response;
    final code = res?.statusCode;
    String? message;

    final body = res?.data;
    if (body is Map) {
      message = (body['message'] ?? body['detail'] ?? body['error'])?.toString();
      // FastAPI validation: detail can be a list of {msg,...}
      if (message == null && body['detail'] is List && (body['detail'] as List).isNotEmpty) {
        final first = (body['detail'] as List).first;
        if (first is Map && first['msg'] != null) message = first['msg'].toString();
      }
    } else if (body is String && body.isNotEmpty) {
      message = body;
    }

    message ??= switch (code) {
      400 => 'Invalid request.',
      401 => 'Session expired. Please sign in again.',
      403 => 'You do not have permission to do that.',
      404 => 'Not found.',
      408 => 'Request timed out.',
      422 => 'Some fields are invalid.',
      500 || 502 || 503 => 'Server error. Please try again later.',
      _ => switch (e.type) {
          DioExceptionType.connectionTimeout ||
          DioExceptionType.sendTimeout ||
          DioExceptionType.receiveTimeout =>
            'Connection timed out.',
          DioExceptionType.connectionError =>
            'Cannot reach the server. Check your connection.',
          _ => 'Something went wrong.',
        },
    };

    return ApiException(message, statusCode: code, data: body);
  }
}
