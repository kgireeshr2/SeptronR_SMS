import 'dart:io';

import 'package:dio/dio.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Background handler must be a top-level function.
@pragma('vm:entry-point')
Future<void> _bgHandler(RemoteMessage message) async {
  // No-op: the OS shows the notification; tap routing happens on open.
}

/// FCM push integration. All calls are guarded so the app runs even when
/// Firebase native config (google-services.json / GoogleService-Info.plist) is
/// absent — push simply stays disabled in that case.
class PushService {
  PushService._();
  static final PushService instance = PushService._();

  final _local = FlutterLocalNotificationsPlugin();
  bool _ready = false;

  Future<void> init() async {
    try {
      await Firebase.initializeApp();
      FirebaseMessaging.onBackgroundMessage(_bgHandler);

      await FirebaseMessaging.instance.requestPermission();

      const android = AndroidInitializationSettings('@mipmap/ic_launcher');
      const ios = DarwinInitializationSettings();
      await _local.initialize(
        const InitializationSettings(android: android, iOS: ios),
      );

      // Foreground messages → show a local notification.
      FirebaseMessaging.onMessage.listen(_showLocal);
      _ready = true;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('PushService disabled (no Firebase config?): $e');
      }
      _ready = false;
    }
  }

  Future<void> _showLocal(RemoteMessage message) async {
    final n = message.notification;
    if (n == null) return;
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'sms_default',
        'General',
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: DarwinNotificationDetails(),
    );
    await _local.show(
      n.hashCode,
      n.title,
      n.body,
      details,
    );
  }

  /// Register this device's FCM token with the backend (`POST /devices/register`).
  Future<void> registerToken(Dio dio) async {
    if (!_ready) return;
    try {
      final token = await FirebaseMessaging.instance.getToken();
      if (token == null) return;
      await _send(dio, '/devices/register', token);
      FirebaseMessaging.instance.onTokenRefresh.listen((t) {
        _send(dio, '/devices/register', t).catchError((_) {});
      });
    } catch (_) {/* best-effort */}
  }

  Future<void> unregister(Dio dio) async {
    if (!_ready) return;
    try {
      final token = await FirebaseMessaging.instance.getToken();
      if (token != null) await _send(dio, '/devices/unregister', token);
    } catch (_) {/* best-effort */}
  }

  Future<void> _send(Dio dio, String path, String token) async {
    await dio.post(path, data: {
      'token': token,
      'provider': 'fcm',
      'platform': Platform.isIOS ? 'ios' : 'android',
    });
  }
}
