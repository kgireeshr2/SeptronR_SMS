import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../core/providers.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../profile/application/identity_providers.dart';
import '../../profile/presentation/child_switcher.dart';
import '../data/ptm_repository.dart';

final _ptmRepoProvider = Provider<PtmRepository>((ref) {
  return PtmRepository(ref.watch(dioProvider));
});

final _ptmEventsProvider = FutureProvider.autoDispose<List<PtmEvent>>((ref) {
  return ref.watch(_ptmRepoProvider).events();
});

final _ptmSlotsProvider =
    FutureProvider.family.autoDispose<List<PtmSlot>, String>((ref, eventId) {
  return ref.watch(_ptmRepoProvider).slots(eventId);
});

class PtmScreen extends ConsumerWidget {
  const PtmScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_ptmEventsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Parent–Teacher Meetings')),
      body: Column(
        children: [
          const ChildSwitcher(),
          Expanded(
            child: async.when(
              loading: () => const LoadingView(),
              error: (e, _) => ErrorView(
                message: e.toString(),
                onRetry: () => ref.invalidate(_ptmEventsProvider),
              ),
              data: (events) {
                if (events.isEmpty) {
                  return const EmptyView(
                      message: 'No PTM events scheduled',
                      icon: Icons.groups_outlined);
                }
                return ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: events.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (_, i) {
                    final e = events[i];
                    return Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.gray200),
                      ),
                      child: ListTile(
                        leading: const Icon(Icons.groups_outlined,
                            color: AppColors.primary),
                        title: Text(e.title,
                            style:
                                const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle:
                            e.date != null ? Text(Fmt.date(e.date)) : null,
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => Navigator.of(context).push(
                          MaterialPageRoute(
                              builder: (_) => _SlotsScreen(event: e)),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _SlotsScreen extends ConsumerWidget {
  const _SlotsScreen({required this.event});
  final PtmEvent event;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_ptmSlotsProvider(event.id));
    return Scaffold(
      appBar: AppBar(title: Text(event.title)),
      body: async.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(_ptmSlotsProvider(event.id)),
        ),
        data: (slots) {
          if (slots.isEmpty) {
            return const EmptyView(message: 'No slots available');
          }
          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: slots.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final s = slots[i];
              final time =
                  '${Fmt.time(s.start)} – ${Fmt.time(s.end)}';
              return Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.gray200),
                ),
                child: ListTile(
                  leading: const Icon(Icons.schedule),
                  title: Text(time),
                  trailing: s.isBooked
                      ? const AppBadge(text: 'Booked', color: AppColors.gray500)
                      : FilledButton(
                          onPressed: () => _book(context, ref, s),
                          child: const Text('Book'),
                        ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Future<void> _book(BuildContext context, WidgetRef ref, PtmSlot slot) async {
    final studentId = ref.read(currentStudentIdProvider);
    if (studentId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Select a child to book a slot.')));
      return;
    }
    try {
      await ref
          .read(_ptmRepoProvider)
          .book(slotId: slot.id, studentId: studentId);
      ref.invalidate(_ptmSlotsProvider(event.id));
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Slot booked'), backgroundColor: AppColors.success));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.toString()), backgroundColor: AppColors.danger));
      }
    }
  }
}
