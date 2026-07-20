/// App configuration. Values are provided at build time via `--dart-define`
/// (e.g. `flutter run --dart-define=APP_API_URL=http://10.0.2.2:8000`) and fall
/// back to sensible dev defaults. No bundled .env file is required.
class Env {
  /// Backend base URL WITHOUT the `/api/v1` suffix.
  static const String apiBaseUrl = String.fromEnvironment(
    'APP_API_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// Full API v1 root, e.g. `http://localhost:8000/api/v1`.
  static String get apiV1 => '$apiBaseUrl/api/v1';

  static const String appEnv =
      String.fromEnvironment('APP_ENV', defaultValue: 'development');

  static bool get isProduction => appEnv == 'production';
}
