import 'dart:async';

import 'package:dio/dio.dart';

import '../config/env.dart';
import '../storage/secure_storage.dart';
import 'auth_events.dart';

/// Builds the app-wide [Dio] instance with three interceptors that mirror the
/// Expo client (`mobile/services/api.ts`):
///   1. inject `Authorization: Bearer` + `X-School-Slug`
///   2. unwrap the `{ success, data }` envelope
///   3. on 401, silently refresh the access token (single-flight) and retry
class DioClient {
  DioClient(this._storage) {
    dio = Dio(
      BaseOptions(
        baseUrl: Env.apiV1,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        // We handle non-2xx ourselves via the error interceptor.
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: _onRequest,
        onResponse: _onResponse,
        onError: _onError,
      ),
    );
  }

  final SecureStorage _storage;
  late final Dio dio;

  // Single-flight refresh coordination.
  Completer<String?>? _refreshCompleter;

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.accessToken;
    final slug = await _storage.schoolSlug;
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    if (slug != null && slug.isNotEmpty) {
      options.headers['X-School-Slug'] = slug;
    }
    handler.next(options);
  }

  void _onResponse(Response response, ResponseInterceptorHandler handler) {
    response.data = unwrapEnvelope(response.data);
    handler.next(response);
  }

  /// Unwraps `{ success: true, data: T }` → `T`. Leaves raw arrays/objects as-is.
  static dynamic unwrapEnvelope(dynamic body) {
    if (body is Map &&
        body['success'] == true &&
        body.containsKey('data')) {
      return body['data'];
    }
    return body;
  }

  Future<void> _onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final response = err.response;
    final request = err.requestOptions;
    final isRefreshCall = request.path.contains('/auth/refresh');
    final alreadyRetried = request.extra['__retried'] == true;

    if (response?.statusCode == 401 && !isRefreshCall && !alreadyRetried) {
      try {
        final newToken = await _refreshAccessToken();
        if (newToken == null || newToken.isEmpty) {
          AuthEvents.instance.emitForceLogout();
          return handler.next(err);
        }
        // Retry the original request with the new token.
        request.extra['__retried'] = true;
        request.headers['Authorization'] = 'Bearer $newToken';
        final retryResponse = await dio.fetch(request);
        return handler.resolve(retryResponse);
      } catch (_) {
        AuthEvents.instance.emitForceLogout();
        return handler.next(err);
      }
    }

    handler.next(err);
  }

  /// Single-flight refresh: concurrent 401s await the same refresh.
  Future<String?> _refreshAccessToken() {
    if (_refreshCompleter != null) return _refreshCompleter!.future;

    final completer = Completer<String?>();
    _refreshCompleter = completer;

    _doRefresh().then((token) {
      completer.complete(token);
    }).catchError((Object e) {
      completer.completeError(e);
    }).whenComplete(() {
      _refreshCompleter = null;
    });

    return completer.future;
  }

  Future<String?> _doRefresh() async {
    final refresh = await _storage.refreshToken;
    if (refresh == null || refresh.isEmpty) {
      throw StateError('No refresh token');
    }

    // Bare dio (no interceptors) — backend reads the HttpOnly cookie, so we
    // replay it as a Cookie header. Mirrors the Expo refresh path.
    final bare = Dio(BaseOptions(baseUrl: Env.apiV1));
    final res = await bare.post(
      '/auth/refresh',
      options: Options(headers: {'Cookie': 'refresh_token=$refresh'}),
    );

    final data = unwrapEnvelope(res.data);
    String? newToken;
    if (data is Map) {
      newToken = (data['access_token'] ?? data['data']?['access_token'])?.toString();
    } else if (data is String) {
      newToken = data;
    }

    if (newToken == null || newToken.isEmpty) {
      await _storage.clearTokens();
      throw StateError('No access token in refresh response');
    }

    await _storage.setAccessToken(newToken);
    return newToken;
  }
}
