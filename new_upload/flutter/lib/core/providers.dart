import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../shared/utils/file_download.dart';
import 'network/dio_client.dart';
import 'storage/secure_storage.dart';

/// Core singletons exposed to the whole app.

final secureStorageProvider = Provider<SecureStorage>((ref) {
  return SecureStorage();
});

final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient(ref.watch(secureStorageProvider));
});

/// The configured [Dio] instance used by every repository.
final dioProvider = Provider<Dio>((ref) {
  return ref.watch(dioClientProvider).dio;
});

/// Authenticated file downloader (PDF receipts / report cards).
final fileDownloaderProvider = Provider<FileDownloader>((ref) {
  return FileDownloader(ref.watch(dioProvider));
});
