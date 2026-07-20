import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/announcements_repository.dart';
import '../domain/announcement.dart';

final announcementsRepositoryProvider =
    Provider<AnnouncementsRepository>((ref) {
  return AnnouncementsRepository(ref.watch(dioProvider));
});

final announcementsProvider =
    FutureProvider.autoDispose<List<Announcement>>((ref) {
  return ref.watch(announcementsRepositoryProvider).listAnnouncements();
});

final notificationsProvider =
    FutureProvider.autoDispose<List<AppNotification>>((ref) {
  return ref.watch(announcementsRepositoryProvider).listNotifications();
});

/// Unread badge count — kept alive so tabs can show it.
final unreadCountProvider = FutureProvider<int>((ref) {
  return ref.watch(announcementsRepositoryProvider).unreadCount();
});
