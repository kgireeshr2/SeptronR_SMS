import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../application/homework_providers.dart';
import '../domain/homework.dart';

class HomeworkSubmissionsScreen extends ConsumerWidget {
  const HomeworkSubmissionsScreen({super.key, required this.homework});
  final Homework homework;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(homeworkSubmissionsProvider(homework.id));
    return Scaffold(
      appBar: AppBar(title: Text(homework.title)),
      body: async.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(homeworkSubmissionsProvider(homework.id)),
        ),
        data: (subs) {
          if (subs.isEmpty) {
            return const EmptyView(
                message: 'No submissions yet', icon: Icons.assignment_outlined);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: subs.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, i) => _SubmissionCard(
              sub: subs[i],
              onGrade: () => _grade(context, ref, subs[i]),
            ),
          );
        },
      ),
    );
  }

  void _grade(BuildContext context, WidgetRef ref, HomeworkSubmission sub) {
    final marks = TextEditingController(text: sub.marksGiven?.toString());
    final remarks = TextEditingController(text: sub.remarks);
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
            Text('Grade — ${sub.studentName ?? 'Student'}',
                style:
                    const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            TextField(
              controller: marks,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Marks'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: remarks,
              maxLines: 2,
              decoration: const InputDecoration(labelText: 'Remarks'),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () async {
                await ref.read(homeworkRepositoryProvider).grade(
                      sub.id,
                      marks: int.tryParse(marks.text.trim()),
                      remarks:
                          remarks.text.trim().isEmpty ? null : remarks.text.trim(),
                    );
                ref.invalidate(homeworkSubmissionsProvider(homework.id));
                if (context.mounted) Navigator.pop(context);
              },
              child: const Text('Save grade'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SubmissionCard extends StatelessWidget {
  const _SubmissionCard({required this.sub, required this.onGrade});
  final HomeworkSubmission sub;
  final VoidCallback onGrade;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.gray200),
      ),
      child: ListTile(
        title: Text(sub.studentName ?? sub.studentId ?? 'Student',
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (sub.content != null)
              Text(sub.content!,
                  maxLines: 2, overflow: TextOverflow.ellipsis),
            if (sub.submittedAt != null)
              Text('Submitted ${Fmt.relative(sub.submittedAt)}',
                  style: const TextStyle(
                      color: AppColors.gray500, fontSize: 12)),
          ],
        ),
        trailing: sub.isGraded
            ? AppBadge(text: '${sub.marksGiven}', color: AppColors.success)
            : TextButton(onPressed: onGrade, child: const Text('Grade')),
        onTap: onGrade,
      ),
    );
  }
}
