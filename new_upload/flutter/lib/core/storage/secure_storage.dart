import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants.dart';

/// Thin wrapper over flutter_secure_storage for auth tokens + tenant slug.
/// Backed by Keychain (iOS) / Keystore-encrypted prefs (Android).
class SecureStorage {
  SecureStorage([FlutterSecureStorage? storage])
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  final FlutterSecureStorage _storage;

  Future<String?> get accessToken => _storage.read(key: kTokenKey);
  Future<String?> get refreshToken => _storage.read(key: kRefreshTokenKey);
  Future<String?> get schoolSlug => _storage.read(key: kSchoolSlugKey);

  Future<void> setAccessToken(String token) =>
      _storage.write(key: kTokenKey, value: token);

  Future<void> setRefreshToken(String token) =>
      _storage.write(key: kRefreshTokenKey, value: token);

  Future<void> setSchoolSlug(String? slug) async {
    if (slug == null || slug.isEmpty) {
      await _storage.delete(key: kSchoolSlugKey);
    } else {
      await _storage.write(key: kSchoolSlugKey, value: slug);
    }
  }

  // Generic helpers for misc small values (e.g. UI prefs, selections).
  Future<String?> read(String key) => _storage.read(key: key);
  Future<void> write(String key, String value) =>
      _storage.write(key: key, value: value);
  Future<void> remove(String key) => _storage.delete(key: key);

  Future<void> clearTokens() async {
    await _storage.delete(key: kTokenKey);
    await _storage.delete(key: kRefreshTokenKey);
  }

  Future<void> clearAll() => _storage.deleteAll();
}
