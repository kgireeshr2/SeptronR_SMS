import 'dart:io';

import 'package:dio/dio.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

import '../../core/network/api_exception.dart';

/// Downloads an authenticated file (PDF, etc.) via the app [Dio] instance to a
/// temp file and opens it with the platform viewer. Reused by fee receipts and
/// exam report cards. (Mobile-only — uses dart:io.)
class FileDownloader {
  FileDownloader(this._dio);
  final Dio _dio;

  /// [path] is an API path relative to `/api/v1`
  /// (e.g. `/exams/{id}/report-card/{studentId}/pdf`).
  Future<void> openPdf(String path, String filename) async {
    try {
      final res = await _dio.get<List<int>>(
        path,
        options: Options(responseType: ResponseType.bytes),
      );
      final dir = await getTemporaryDirectory();
      final safe = filename.endsWith('.pdf') ? filename : '$filename.pdf';
      final file = File('${dir.path}/$safe');
      await file.writeAsBytes(res.data ?? const [], flush: true);
      await OpenFilex.open(file.path);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
