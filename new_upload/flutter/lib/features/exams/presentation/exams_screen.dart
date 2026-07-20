import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../core/providers.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../auth/application/auth_controller.dart';
import '../../profile/application/identity_providers.dart';
import '../application/exams_providers.dart';
import '../domain/exam.dart';

class ExamsScreen extends ConsumerWidget {
  const ExamsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(examsListProvider);
    final canMark = ref.watch(authControllerProvider).can('exams', 'manage');

    return Scaffold(
      appBar: AppBar(title: const Text('Exams')),
      body: async.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(examsListProvider),
        ),
        data: (exams) {
          if (exams.isEmpty) {
            return const EmptyView(message: 'No exams scheduled');
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(examsListProvider),
            child: ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: exams.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (_, i) {
                final e = exams[i];
                return Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.gray200),
                  ),
                  child: ListTile(
                    title: Text(e.name,
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: Text([
                      if (e.examTypeName != null) e.examTypeName,
                      if (e.subjectName != null) e.subjectName,
                      if (e.className != null) e.className,
                      if (e.date != null) Fmt.date(e.date),
                    ].whereType<String>().join(' · ')),
                    trailing: canMark
                        ? const Icon(Icons.edit_outlined,
                            color: AppColors.primary)
                        : const Icon(Icons.picture_as_pdf_outlined,
                            color: AppColors.danger),
                    onTap: () => canMark
                        ? Navigator.of(context).push(MaterialPageRoute(
                            builder: (_) => ExamMarksScreen(exam: e)))
                        : _openReportCard(context, ref, e),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }

  Future<void> _openReportCard(
      BuildContext context, WidgetRef ref, Exam exam) async {
    final studentId = ref.read(currentStudentIdProvider);
    if (studentId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Report card needs a linked student profile.'),
      ));
      return;
    }
    final repo = ref.read(examsRepositoryProvider);
    ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Opening report card…')));
    try {
      await ref.read(fileDownloaderProvider).openPdf(
            repo.reportCardPath(exam.id, studentId),
            'report_card_${exam.name}',
          );
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.toString()), backgroundColor: AppColors.danger));
      }
    }
  }
}

/// Teacher/admin: view + enter marks for an exam.
class ExamMarksScreen extends ConsumerStatefulWidget {
  const ExamMarksScreen({super.key, required this.exam});
  final Exam exam;

  @override
  ConsumerState<ExamMarksScreen> createState() => _ExamMarksScreenState();
}

class _ExamMarksScreenState extends ConsumerState<ExamMarksScreen> {
  final Map<String, String> _edited = {}; // studentId -> marks text
  bool _saving = false;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final entries = _edited.entries
          .where((e) => e.value.trim().isNotEmpty)
          .map((e) => {
                'student_id': e.key,
                'marks_obtained': double.tryParse(e.value.trim()),
              })
          .where((m) => m['marks_obtained'] != null)
          .toList();
      if (entries.isEmpty) {
        _snack('Enter at least one mark', AppColors.warning);
        return;
      }
      await ref
          .read(examsRepositoryProvider)
          .enterMarks(widget.exam.id, entries);
      ref.invalidate(examMarksProvider(widget.exam.id));
      _edited.clear();
      _snack('Marks saved', AppColors.success);
    } catch (e) {
      _snack(e.toString(), AppColors.danger);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _snack(String m, Color c) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(m), backgroundColor: c));
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(examMarksProvider(widget.exam.id));
    return Scaffold(
      appBar: AppBar(title: Text(widget.exam.name)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _saving ? null : _save,
        icon: _saving
            ? const SizedBox(
                height: 18,
                width: 18,
                child: CircularProgressIndicator(
                    strokeWidth: 2.2, color: Colors.white))
            : const Icon(Icons.save),
        label: const Text('Save marks'),
      ),
      body: async.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(examMarksProvider(widget.exam.id)),
        ),
        data: (marks) {
          if (marks.isEmpty) {
            return const EmptyView(message: 'No students for this exam');
          }
          final full = marks.first.fullMarks;
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 96),
            itemCount: marks.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (_, i) {
              final m = marks[i];
              return ListTile(
                title: Text(m.studentName),
                subtitle: m.admissionNumber != null
                    ? Text(m.admissionNumber!)
                    : null,
                trailing: SizedBox(
                  width: 92,
                  child: TextFormField(
                    initialValue: m.marksObtained?.toStringAsFixed(0),
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    decoration: InputDecoration(
                      isDense: true,
                      suffixText: full != null ? '/$full' : null,
                    ),
                    onChanged: (v) => _edited[m.studentId] = v,
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
