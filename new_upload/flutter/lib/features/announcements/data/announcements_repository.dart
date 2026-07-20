import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/announcement.dart';

class AnnouncementsRepository {
  AnnouncementsRepository(this._dio);
  final Dio _dio;

  Future<List<Announcement>> listAnnouncements() async {
    try {
      final res = await _dio.get('/announcements');
      return Paginated.fromJson(res.data, Announcement.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// `POST /announcements` { title, body, audience }. (communications:write)
  Future<void> create({
    required String title,
    required String body,
    String audience = 'all',
  }) async {
    try {
      await _dio.post('/announcements',
          data: {'title': title, 'body': body, 'audience': audience});
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<AppNotification>> listNotifications() async {
    try {
      final res = await _dio.get('/notifications');
      return Paginated.fromJson(res.data, AppNotification.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// `POST /notifications/mark-read` with `{ notification_ids: [...] }`.
  Future<void> markNotificationRead(String id) async {
    try {
      await _dio.post('/notifications/mark-read',
          data: {'notification_ids': [id]});
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<void> markAllNotificationsRead() async {
    try {
      await _dio.post('/notifications/mark-all-read');
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// No unread-count endpoint exists — derive from the notification list.
  Future<int> unreadCount() async {
    try {
      final items = await listNotifications();
      return items.where((n) => !n.isRead).length;
    } catch (_) {
      return 0;
    }
  }
}
