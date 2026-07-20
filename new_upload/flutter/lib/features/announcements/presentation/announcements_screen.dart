import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../auth/application/auth_controller.dart';
import '../application/announcements_providers.dart';
import '../domain/announcement.dart';

class AnnouncementsScreen extends ConsumerWidget {
  const AnnouncementsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final canPost =
        ref.watch(authControllerProvider).can('communications', 'write');
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Notices'),
          bottom: const TabBar(
            indicatorColor: Colors.white,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            tabs: [Tab(text: 'Announcements'), Tab(text: 'Notifications')],
          ),
        ),
        floatingActionButton: canPost
            ? FloatingActionButton.extended(
                onPressed: () => _post(context, ref),
                icon: const Icon(Icons.add),
                label: const Text('Post'),
              )
            : null,
        body: const TabBarView(
          children: [_AnnouncementsTab(), _NotificationsTab()],
        ),
      ),
    );
  }

  void _post(BuildContext context, WidgetRef ref) {
    final title = TextEditingController();
    final body = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => Padding(
        padding: EdgeInsets.fromLTRB(
            20, 0, 20, MediaQuery.of(context).viewInsets.bottom + 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('New announcement',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            TextField(
              controller: title,
              decoration: const InputDecoration(labelText: 'Title'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: body,
              maxLines: 4,
              decoration: const InputDecoration(
                  labelText: 'Message', alignLabelWithHint: true),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () async {
                if (title.text.trim().isEmpty || body.text.trim().isEmpty) {
                  return;
                }
                try {
                  await ref.read(announcementsRepositoryProvider).create(
                        title: title.text.trim(),
                        body: body.text.trim(),
                      );
                  ref.invalidate(announcementsProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                        content: Text(e.toString()),
                        backgroundColor: AppColors.danger));
                  }
                }
              },
              child: const Text('Publish'),
            ),
          ],
        ),
      ),
    );
  }
}

class _AnnouncementsTab extends ConsumerWidget {
  const _AnnouncementsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(announcementsProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(announcementsProvider),
      ),
      data: (items) {
        if (items.isEmpty) {
          return const EmptyView(message: 'No announcements yet');
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(announcementsProvider),
          child: ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, i) =>
                _AnnouncementCard(item: items[i]),
          ),
        );
      },
    );
  }
}

class _AnnouncementCard extends StatelessWidget {
  const _AnnouncementCard({required this.item});
  final Announcement item;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.gray200),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        leading: CircleAvatar(
          backgroundColor: AppColors.primaryLight.withOpacity(0.15),
          child: const Icon(Icons.campaign_outlined, color: AppColors.primary),
        ),
        title: Text(item.title,
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (item.content != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(item.content!,
                    maxLines: 2, overflow: TextOverflow.ellipsis),
              ),
            const SizedBox(height: 6),
            Text(
              '${item.createdByName ?? ''}'
              '${item.publishedAt != null ? ' · ${Fmt.relative(item.publishedAt)}' : ''}',
              style: const TextStyle(color: AppColors.gray500, fontSize: 12),
            ),
          ],
        ),
        onTap: () => _open(context),
      ),
    );
  }

  void _open(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        maxChildSize: 0.9,
        initialChildSize: 0.6,
        builder: (_, controller) => ListView(
          controller: controller,
          padding: const EdgeInsets.all(20),
          children: [
            Text(item.title,
                style: const TextStyle(
                    fontSize: 20, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Text(
              '${item.createdByName ?? ''}'
              '${item.publishedAt != null ? ' · ${Fmt.dateTime(item.publishedAt)}' : ''}',
              style: const TextStyle(color: AppColors.gray500),
            ),
            const Divider(height: 24),
            Text(item.content ?? 'No content', style: const TextStyle(fontSize: 15, height: 1.4)),
          ],
        ),
      ),
    );
  }
}

class _NotificationsTab extends ConsumerWidget {
  const _NotificationsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(notificationsProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(notificationsProvider),
      ),
      data: (items) {
        if (items.isEmpty) {
          return const EmptyView(
              message: 'No notifications', icon: Icons.notifications_none);
        }
        return Column(
          children: [
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () async {
                  await ref
                      .read(announcementsRepositoryProvider)
                      .markAllNotificationsRead();
                  ref.invalidate(notificationsProvider);
                  ref.invalidate(unreadCountProvider);
                },
                icon: const Icon(Icons.done_all, size: 18),
                label: const Text('Mark all read'),
              ),
            ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async => ref.invalidate(notificationsProvider),
                child: ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) {
                    final n = items[i];
                    return ListTile(
                      leading: Icon(
                        n.isRead
                            ? Icons.notifications_none
                            : Icons.notifications_active,
                        color: n.isRead ? AppColors.gray500 : AppColors.primary,
                      ),
                      title: Text(n.title,
                          style: TextStyle(
                              fontWeight: n.isRead
                                  ? FontWeight.w400
                                  : FontWeight.w700)),
                      subtitle: Text(n.message ?? ''),
                      trailing: Text(Fmt.relative(n.createdAt),
                          style: const TextStyle(
                              color: AppColors.gray500, fontSize: 11)),
                      onTap: () async {
                        if (!n.isRead) {
                          await ref
                              .read(announcementsRepositoryProvider)
                              .markNotificationRead(n.id);
                          ref.invalidate(notificationsProvider);
                          ref.invalidate(unreadCountProvider);
                        }
                      },
                    );
                  },
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}
