import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../shared/models/login_response.dart';
import '../../../shared/models/user.dart';

/// All `/auth/*` calls. Persists tokens + school slug as a side effect of
/// login/otp so the dio interceptor can authenticate subsequent requests.
class AuthRepository {
  AuthRepository(this._dio, this._storage);

  final Dio _dio;
  final SecureStorage _storage;

  Future<LoginResponse> login({
    required String identifier,
    required String password,
    String? schoolSlug,
  }) async {
    return _authenticate(
      path: '/auth/login',
      body: {'identifier': identifier, 'password': password},
      schoolSlug: schoolSlug,
    );
  }

  Future<void> sendOtp(String phone, {String? schoolSlug}) async {
    try {
      await _dio.post(
        '/auth/send-otp',
        data: {'phone': phone},
        options: _slugOptions(schoolSlug),
      );
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<LoginResponse> verifyOtp({
    required String phone,
    required String otp,
    String? schoolSlug,
  }) async {
    return _authenticate(
      path: '/auth/verify-otp',
      body: {'phone': phone, 'otp': otp},
      schoolSlug: schoolSlug,
    );
  }

  Future<User> me() async {
    try {
      final res = await _dio.get('/auth/me');
      return User.fromJson(Map<String, dynamic>.from(res.data as Map));
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } catch (_) {
      // Best-effort; tokens are cleared by the caller regardless.
    } finally {
      await _storage.clearTokens();
    }
  }

  Future<void> forgotPassword(String email) async {
    try {
      await _dio.post('/auth/forgot-password', data: {'email': email});
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<void> resetPassword(String token, String newPassword) async {
    try {
      await _dio.post(
        '/auth/reset-password',
        data: {'token': token, 'new_password': newPassword},
      );
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<void> changePassword(String current, String newPassword) async {
    try {
      await _dio.post(
        '/auth/change-password',
        data: {'current_password': current, 'new_password': newPassword},
      );
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  // ── internals ──────────────────────────────────────────────────────────

  Options _slugOptions(String? slug) => Options(
        headers: {
          if (slug != null && slug.isNotEmpty) 'X-School-Slug': slug,
        },
      );

  /// Shared path for login + verify-otp: posts credentials, captures the
  /// access token (body) and refresh token (Set-Cookie header), persists both.
  Future<LoginResponse> _authenticate({
    required String path,
    required Map<String, dynamic> body,
    String? schoolSlug,
  }) async {
    try {
      if (schoolSlug != null && schoolSlug.isNotEmpty) {
        await _storage.setSchoolSlug(schoolSlug);
      }

      final res = await _dio.post(
        path,
        data: body,
        options: _slugOptions(schoolSlug),
      );

      // `res.data` is already envelope-unwrapped by the interceptor.
      final data = Map<String, dynamic>.from(res.data as Map);
      final login = LoginResponse.fromJson(data);

      await _storage.setAccessToken(login.accessToken);

      final refresh = _extractRefreshToken(res.headers);
      if (refresh != null && refresh.isNotEmpty) {
        await _storage.setRefreshToken(refresh);
      }

      // Prefer the slug the server confirms.
      final confirmedSlug = login.school?.slug ?? schoolSlug;
      if (confirmedSlug != null && confirmedSlug.isNotEmpty) {
        await _storage.setSchoolSlug(confirmedSlug);
      }

      return login;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// The backend sets `refresh_token` as an HttpOnly cookie. On mobile we read
  /// it from the Set-Cookie header at login and replay it on `/auth/refresh`.
  static String? _extractRefreshToken(Headers headers) {
    final cookies = headers.map['set-cookie'];
    if (cookies == null) return null;
    for (final c in cookies) {
      final m = RegExp(r'refresh_token=([^;]+)').firstMatch(c);
      if (m != null) return m.group(1);
    }
    return null;
  }
}
