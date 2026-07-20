import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/skeleton.dart';
import '../../auth/application/auth_controller.dart';
import '../../profile/application/identity_providers.dart';
import '../application/homework_providers.dart';
import '../domain/homework.dart';
import 'homework_submissions_screen.dart';

class HomeworkScreen extends ConsumerWidget {
  const HomeworkScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(homeworkListProvider);
    final canCreate = ref.watch(authControllerProvider).can('homework', 'create');

    return Scaffold(
      appBar: AppBar(title: const Text('Homework')),
      floatingActionButton: canCreate
          ? FloatingActionButton.extended(
              onPressed: () => _openCreate(context, ref),
              icon: const Icon(Icons.add),
              label: const Text('Assign'),
            )
          : null,
      body: async.when(
        loading: () => const SkeletonList(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(homeworkListProvider),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const EmptyView(
                message: 'No homework assigned', icon: Icons.description_outlined);
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(homeworkListProvider),
            child: ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (_, i) => _HomeworkCard(
                hw: items[i],
                canDelete: canCreate,
                onTap: () => _openDetail(context, ref, items[i], canCreate),
              ),
            ),
          );
        },
      ),
    );
  }

  void _openDetail(
      BuildContext context, WidgetRef ref, Homework hw, bool canDelete) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(hw.title,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Wrap(spacing: 8, children: [
              if (hw.subjectName != null) AppBadge(text: hw.subjectName!, color: AppColors.info),
              if (hw.className != null) AppBadge(text: hw.className!, color: AppColors.primary),
              if (hw.dueDate != null)
                AppBadge(
                  text: 'Due ${Fmt.date(hw.dueDate)}',
                  color: hw.isOverdue ? AppColors.danger : AppColors.warning,
                ),
            ]),
            const Divider(height: 24),
            Text(hw.description ?? 'No description',
                style: const TextStyle(fontSize: 15, height: 1.4)),
            if (hw.assignedByName != null) ...[
              const SizedBox(height: 16),
              Text('Assigned by ${hw.assignedByName}',
                  style: const TextStyle(color: AppColors.gray500)),
            ],
            if (canDelete) ...[
              const SizedBox(height: 16),
              FilledButton.tonalIcon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => HomeworkSubmissionsScreen(homework: hw),
                  ));
                },
                icon: const Icon(Icons.assignment_turned_in_outlined),
                label: const Text('View submissions'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
                onPressed: () async {
                  Navigator.pop(context);
                  await ref.read(homeworkRepositoryProvider).delete(hw.id);
                  ref.invalidate(homeworkListProvider);
                },
                icon: const Icon(Icons.delete_outline),
                label: const Text('Delete'),
              ),
            ] else if (ref.read(currentStudentIdProvider) != null) ...[
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  _openSubmit(context, ref, hw);
                },
                icon: const Icon(Icons.upload_file_outlined),
                label: const Text('Submit homework'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _openSubmit(BuildContext context, WidgetRef ref, Homework hw) {
    final content = TextEditingController();
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
            Text('Submit — ${hw.title}',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            TextField(
              controller: content,
              maxLines: 4,
              decoration: const InputDecoration(
                  labelText: 'Your answer / notes',
                  alignLabelWithHint: true),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () async {
                final studentId = ref.read(currentStudentIdProvider);
                if (studentId == null) return;
                try {
                  await ref.read(homeworkRepositoryProvider).submit(
                        homeworkId: hw.id,
                        studentId: studentId,
                        content: content.text.trim(),
                      );
                  if (context.mounted) {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                        content: Text('Submitted'),
                        backgroundColor: AppColors.success));
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                        content: Text(e.toString()),
                        backgroundColor: AppColors.danger));
                  }
                }
              },
              child: const Text('Submit'),
            ),
          ],
        ),
      ),
    );
  }

  void _openCreate(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: const _CreateHomeworkSheet(),
      ),
    );
  }
}

class _HomeworkCard extends StatelessWidget {
  const _HomeworkCard({
    required this.hw,
    required this.canDelete,
    required this.onTap,
  });
  final Homework hw;
  final bool canDelete;
  final VoidCallback onTap;

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
        title: Text(hw.title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Text(
            [
              if (hw.subjectName != null) hw.subjectName,
              if (hw.className != null) hw.className,
            ].whereType<String>().join(' · '),
            style: const TextStyle(color: AppColors.gray500),
          ),
        ),
        trailing: hw.dueDate == null
            ? null
            : AppBadge(
                text: Fmt.date(hw.dueDate),
                color: hw.isOverdue ? AppColors.danger : AppColors.warning,
              ),
        onTap: onTap,
      ),
    );
  }
}

class _CreateHomeworkSheet extends ConsumerStatefulWidget {
  const _CreateHomeworkSheet();

  @override
  ConsumerState<_CreateHomeworkSheet> createState() =>
      _CreateHomeworkSheetState();
}

class _CreateHomeworkSheetState extends ConsumerState<_CreateHomeworkSheet> {
  final _title = TextEditingController();
  final _desc = TextEditingController();
  DateTime? _due;
  bool _busy = false;

  @override
  void dispose() {
    _title.dispose();
    _desc.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_title.text.trim().isEmpty) return;
    setState(() => _busy = true);
    try {
      await ref.read(homeworkRepositoryProvider).create(
            title: _title.text.trim(),
            description: _desc.text.trim().isEmpty ? null : _desc.text.trim(),
            dueDate: _due,
          );
      ref.invalidate(homeworkListProvider);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: AppColors.danger),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Assign homework',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          TextField(
            controller: _title,
            decoration: const InputDecoration(labelText: 'Title'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _desc,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'Description'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: DateTime.now(),
                firstDate: DateTime.now().subtract(const Duration(days: 1)),
                lastDate: DateTime.now().add(const Duration(days: 365)),
              );
              if (picked != null) setState(() => _due = picked);
            },
            icon: const Icon(Icons.event),
            label: Text(_due == null ? 'Set due date' : 'Due ${Fmt.date(_due)}'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _busy ? null : _save,
            child: _busy
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                        strokeWidth: 2.4, color: Colors.white))
                : const Text('Assign'),
          ),
        ],
      ),
    );
  }
}
