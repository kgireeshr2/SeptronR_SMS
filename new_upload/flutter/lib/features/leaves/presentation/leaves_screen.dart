import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../auth/application/auth_controller.dart';
import '../application/leaves_providers.dart';
import '../domain/leave.dart';

class LeavesScreen extends ConsumerWidget {
  const LeavesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final canApprove =
        auth.can('leaves', 'review') || auth.can('leaves', 'approve');

    return DefaultTabController(
      length: canApprove ? 2 : 1,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Leaves'),
          bottom: TabBar(
            indicatorColor: Colors.white,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            tabs: [
              const Tab(text: 'My leaves'),
              if (canApprove) const Tab(text: 'Approvals'),
            ],
          ),
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: () => _openApply(context, ref),
          icon: const Icon(Icons.add),
          label: const Text('Apply'),
        ),
        body: TabBarView(
          children: [
            const _MyLeaves(),
            if (canApprove) const _Approvals(),
          ],
        ),
      ),
    );
  }

  void _openApply(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => Padding(
        padding:
            EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: const _ApplyLeaveSheet(),
      ),
    );
  }
}

class _MyLeaves extends ConsumerWidget {
  const _MyLeaves();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(myLeavesProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(myLeavesProvider),
      ),
      data: (items) {
        return RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(myLeavesProvider);
            ref.invalidate(myLeaveBalancesProvider);
          },
          child: ListView(
            padding: const EdgeInsets.all(12),
            children: [
              const _BalancesStrip(),
              if (items.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 60),
                  child: EmptyView(message: 'No leave applications'),
                )
              else
                for (final l in items)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: _LeaveCard(
                      leave: l,
                      trailing: l.isPending
                          ? TextButton(
                              onPressed: () async {
                                await ref
                                    .read(leavesRepositoryProvider)
                                    .cancel(l.id);
                                ref.invalidate(myLeavesProvider);
                              },
                              child: const Text('Cancel'),
                            )
                          : AppBadge(text: l.status),
                    ),
                  ),
            ],
          ),
        );
      },
    );
  }
}

class _BalancesStrip extends ConsumerWidget {
  const _BalancesStrip();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(myLeaveBalancesProvider);
    return async.maybeWhen(
      data: (balances) {
        if (balances.isEmpty) return const SizedBox.shrink();
        return SizedBox(
          height: 86,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.only(bottom: 12),
            children: [
              for (final b in balances)
                Container(
                  width: 130,
                  margin: const EdgeInsets.only(right: 10),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.gray200),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('${b.remaining.toStringAsFixed(0)} left',
                          style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                              color: AppColors.primary)),
                      const SizedBox(height: 2),
                      Text(b.leaveTypeName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(color: AppColors.gray500)),
                    ],
                  ),
                ),
            ],
          ),
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}

class _Approvals extends ConsumerWidget {
  const _Approvals();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(pendingLeavesProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(pendingLeavesProvider),
      ),
      data: (items) {
        if (items.isEmpty) {
          return const EmptyView(
              message: 'No pending requests', icon: Icons.task_alt);
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(pendingLeavesProvider),
          child: ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final l = items[i];
              return _LeaveCard(
                leave: l,
                showStaff: true,
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      tooltip: 'Approve',
                      icon: const Icon(Icons.check_circle,
                          color: AppColors.success),
                      onPressed: () async {
                        await ref
                            .read(leavesRepositoryProvider)
                            .review(l.id, approved: true);
                        ref.invalidate(pendingLeavesProvider);
                      },
                    ),
                    IconButton(
                      tooltip: 'Reject',
                      icon: const Icon(Icons.cancel, color: AppColors.danger),
                      onPressed: () async {
                        await ref
                            .read(leavesRepositoryProvider)
                            .review(l.id, approved: false);
                        ref.invalidate(pendingLeavesProvider);
                      },
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }
}

class _LeaveCard extends StatelessWidget {
  const _LeaveCard({
    required this.leave,
    this.trailing,
    this.showStaff = false,
  });
  final LeaveApplication leave;
  final Widget? trailing;
  final bool showStaff;

  @override
  Widget build(BuildContext context) {
    final range = [leave.fromDate, leave.toDate]
        .map((d) => d == null ? null : Fmt.date(d))
        .whereType<String>()
        .join(' → ');
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.gray200),
      ),
      child: ListTile(
        title: Text(
          showStaff
              ? (leave.staffName ?? 'Staff')
              : (leave.leaveTypeName ?? 'Leave'),
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (showStaff && leave.leaveTypeName != null)
              Text(leave.leaveTypeName!),
            if (range.isNotEmpty)
              Text('$range'
                  '${leave.totalDays != null ? ' · ${leave.totalDays!.toStringAsFixed(0)}d' : ''}'),
            if (leave.reason != null)
              Text(leave.reason!,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: AppColors.gray500)),
          ],
        ),
        trailing: trailing,
        isThreeLine: leave.reason != null,
      ),
    );
  }
}

class _ApplyLeaveSheet extends ConsumerStatefulWidget {
  const _ApplyLeaveSheet();

  @override
  ConsumerState<_ApplyLeaveSheet> createState() => _ApplyLeaveSheetState();
}

class _ApplyLeaveSheetState extends ConsumerState<_ApplyLeaveSheet> {
  final _reason = TextEditingController();
  LeaveType? _type;
  DateTime _start = DateTime.now();
  DateTime _end = DateTime.now();
  bool _busy = false;

  @override
  void dispose() {
    _reason.dispose();
    super.dispose();
  }

  double get _days => _end.difference(_start).inDays + 1;

  Future<void> _pick(bool start) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: start ? _start : _end,
      firstDate: DateTime.now().subtract(const Duration(days: 7)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() {
        if (start) {
          _start = picked;
          if (_end.isBefore(_start)) _end = _start;
        } else {
          _end = picked.isBefore(_start) ? _start : picked;
        }
      });
    }
  }

  Future<void> _submit() async {
    if (_type == null) {
      _snack('Select a leave type');
      return;
    }
    setState(() => _busy = true);
    try {
      await ref.read(leavesRepositoryProvider).apply(
            leaveTypeId: _type!.id,
            from: _start,
            to: _end,
            totalDays: _days,
            reason: _reason.text.trim().isEmpty ? null : _reason.text.trim(),
          );
      ref.invalidate(myLeavesProvider);
      ref.invalidate(myLeaveBalancesProvider);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      _snack(e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _snack(String m) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(m), backgroundColor: AppColors.danger));
  }

  @override
  Widget build(BuildContext context) {
    final typesAsync = ref.watch(leaveTypesProvider);
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Apply for leave',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          typesAsync.when(
            loading: () => const LinearProgressIndicator(),
            error: (e, _) => Text('Cannot load leave types: $e',
                style: const TextStyle(color: AppColors.danger)),
            data: (types) => DropdownButtonFormField<LeaveType>(
              value: _type,
              decoration: const InputDecoration(labelText: 'Leave type'),
              items: [
                for (final t in types)
                  DropdownMenuItem(value: t, child: Text(t.name)),
              ],
              onChanged: (v) => setState(() => _type = v),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => _pick(true),
                  child: Text('From ${Fmt.date(_start)}'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton(
                  onPressed: () => _pick(false),
                  child: Text('To ${Fmt.date(_end)}'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text('${_days.toStringAsFixed(0)} day(s)',
              style: const TextStyle(color: AppColors.gray500)),
          const SizedBox(height: 12),
          TextField(
            controller: _reason,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'Reason'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _busy ? null : _submit,
            child: _busy
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                        strokeWidth: 2.4, color: Colors.white))
                : const Text('Submit'),
          ),
        ],
      ),
    );
  }
}
