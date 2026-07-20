import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../academic/application/academic_providers.dart';
import '../../academic/domain/academic_year.dart';
import '../../auth/application/auth_controller.dart';
import '../../profile/application/identity_providers.dart';
import '../../profile/presentation/child_switcher.dart';
import '../../students/application/students_providers.dart';
import '../application/attendance_providers.dart';
import '../domain/attendance.dart';

class AttendanceScreen extends ConsumerWidget {
  const AttendanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final canMark = ref.watch(authControllerProvider).can('attendance', 'mark');
    return Scaffold(
      appBar: AppBar(title: const Text('Attendance')),
      body: canMark ? const _MarkAttendance() : const _StudentAttendanceView(),
    );
  }
}

// ─── Parent/Student: monthly summary for the resolved student ───────────────
class _StudentAttendanceView extends ConsumerWidget {
  const _StudentAttendanceView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final studentId = ref.watch(currentStudentIdProvider);
    final now = DateTime.now();
    final from = DateTime(now.year, now.month, 1);
    final to = DateTime(now.year, now.month + 1, 0);

    Widget body;
    if (studentId == null) {
      body = const EmptyView(
        icon: Icons.event_available_outlined,
        message:
            'Attendance summary will appear here once your student profile is linked.',
      );
    } else {
      final async = ref.watch(
        studentAttendanceProvider(
          StudentMonthKey(studentId: studentId, from: from, to: to),
        ),
      );
      body = async.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(studentAttendanceProvider),
        ),
        data: (s) => _SummaryView(summary: s, monthLabel: Fmt.date(from)),
      );
    }

    return Column(
      children: [const ChildSwitcher(), Expanded(child: body)],
    );
  }
}

class _SummaryView extends StatelessWidget {
  const _SummaryView({required this.summary, required this.monthLabel});
  final AttendanceSummary summary;
  final String monthLabel;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: [
              summary.isLow ? AppColors.danger : AppColors.success,
              (summary.isLow ? AppColors.danger : AppColors.success)
                  .withOpacity(0.7),
            ]),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            children: [
              Text('${summary.attendancePct.toStringAsFixed(1)}%',
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 40,
                      fontWeight: FontWeight.w800)),
              Text('Attendance this month',
                  style: TextStyle(color: Colors.white.withOpacity(0.9))),
            ],
          ),
        ),
        const SizedBox(height: 16),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.7,
          children: [
            _tile('Present', summary.daysPresent, AppColors.success),
            _tile('Absent', summary.daysAbsent, AppColors.danger),
            _tile('Late', summary.daysLate, AppColors.warning),
            _tile('Leave', summary.daysLeave, AppColors.info),
          ],
        ),
        const SizedBox(height: 12),
        Center(
          child: Text('Working days: ${summary.totalWorkingDays}',
              style: const TextStyle(color: AppColors.gray500)),
        ),
      ],
    );
  }

  Widget _tile(String label, int value, Color color) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.gray200),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('$value',
                style: TextStyle(
                    fontSize: 26, fontWeight: FontWeight.w800, color: color)),
            Text(label, style: const TextStyle(color: AppColors.gray500)),
          ],
        ),
      );
}

// ─── Teacher/Admin: mark section attendance ─────────────────────────────────
class _MarkAttendance extends ConsumerStatefulWidget {
  const _MarkAttendance();

  @override
  ConsumerState<_MarkAttendance> createState() => _MarkAttendanceState();
}

class _MarkAttendanceState extends ConsumerState<_MarkAttendance> {
  ClassRoom? _class;
  Section? _section;
  DateTime _date = DateTime.now();
  final Map<String, String> _status = {};
  bool _submitting = false;

  Future<void> _loadExisting() async {
    if (_section == null) return;
    final existing = await ref
        .read(attendanceRepositoryProvider)
        .sectionStatuses(sectionId: _section!.id, date: _date);
    if (mounted) {
      setState(() {
        _status
          ..clear()
          ..addAll(existing);
      });
    }
  }

  Future<void> _submit() async {
    if (_section == null || _status.isEmpty) return;
    final year = await ref.read(currentYearProvider.future);
    if (year == null) {
      _snack('No academic year set', AppColors.danger);
      return;
    }
    setState(() => _submitting = true);
    try {
      await ref.read(attendanceRepositoryProvider).markSection(
            sectionId: _section!.id,
            academicYearId: year.id,
            date: _date,
            statuses: _status,
          );
      _snack('Attendance saved', AppColors.success);
    } catch (e) {
      _snack(e.toString(), AppColors.danger);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _snack(String msg, Color c) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(msg), backgroundColor: c));
  }

  @override
  Widget build(BuildContext context) {
    final classesAsync = ref.watch(classesProvider);

    return Column(
      children: [
        _Selectors(
          classesAsync: classesAsync,
          selectedClass: _class,
          selectedSection: _section,
          date: _date,
          onClass: (c) => setState(() {
            _class = c;
            _section = null;
            _status.clear();
          }),
          onSection: (s) {
            setState(() {
              _section = s;
              _status.clear();
            });
            _loadExisting();
          },
          onDate: (d) {
            setState(() => _date = d);
            _loadExisting();
          },
        ),
        const Divider(height: 1),
        Expanded(child: _studentList()),
        if (_section != null && _status.isNotEmpty)
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: FilledButton(
                onPressed: _submitting ? null : _submit,
                child: _submitting
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            strokeWidth: 2.4, color: Colors.white))
                    : Text('Save attendance (${_status.length})'),
              ),
            ),
          ),
      ],
    );
  }

  Widget _studentList() {
    if (_section == null) {
      return const EmptyView(
          message: 'Select a class and section to mark attendance',
          icon: Icons.checklist_outlined);
    }
    final studentsAsync =
        ref.watch(studentsProvider(StudentQuery(sectionId: _section!.id)));
    return studentsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(message: e.toString()),
      data: (students) {
        if (students.isEmpty) {
          return const EmptyView(message: 'No students in this section');
        }
        for (final s in students) {
          _status.putIfAbsent(s.id, () => AttendanceStatus.present);
        }
        return ListView.separated(
          itemCount: students.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (_, i) {
            final s = students[i];
            return ListTile(
              title: Text(s.fullName),
              subtitle:
                  s.admissionNumber != null ? Text(s.admissionNumber!) : null,
              trailing: _StatusToggle(
                value: _status[s.id] ?? AttendanceStatus.present,
                onChanged: (v) => setState(() => _status[s.id] = v),
              ),
            );
          },
        );
      },
    );
  }
}

class _Selectors extends StatelessWidget {
  const _Selectors({
    required this.classesAsync,
    required this.selectedClass,
    required this.selectedSection,
    required this.date,
    required this.onClass,
    required this.onSection,
    required this.onDate,
  });

  final AsyncValue<List<ClassRoom>> classesAsync;
  final ClassRoom? selectedClass;
  final Section? selectedSection;
  final DateTime date;
  final ValueChanged<ClassRoom?> onClass;
  final ValueChanged<Section?> onSection;
  final ValueChanged<DateTime> onDate;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          classesAsync.when(
            loading: () => const LinearProgressIndicator(),
            error: (e, _) => Text('Cannot load classes: $e',
                style: const TextStyle(color: AppColors.danger)),
            data: (classes) => Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<ClassRoom>(
                    isExpanded: true,
                    value: selectedClass,
                    decoration: const InputDecoration(
                        labelText: 'Class', isDense: true),
                    items: [
                      for (final c in classes)
                        DropdownMenuItem(value: c, child: Text(c.name)),
                    ],
                    onChanged: onClass,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<Section>(
                    isExpanded: true,
                    value: selectedSection,
                    decoration: const InputDecoration(
                        labelText: 'Section', isDense: true),
                    items: [
                      for (final s in selectedClass?.sections ?? const [])
                        DropdownMenuItem(value: s, child: Text(s.name)),
                    ],
                    onChanged: onSection,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.event, size: 18, color: AppColors.gray500),
              const SizedBox(width: 8),
              Text(Fmt.date(date)),
              const Spacer(),
              TextButton(
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: date,
                    firstDate: DateTime.now().subtract(const Duration(days: 60)),
                    lastDate: DateTime.now(),
                  );
                  if (picked != null) onDate(picked);
                },
                child: const Text('Change date'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatusToggle extends StatelessWidget {
  const _StatusToggle({required this.value, required this.onChanged});
  final String value;
  final ValueChanged<String> onChanged;

  static const _opts = [
    (AttendanceStatus.present, 'P', AppColors.success),
    (AttendanceStatus.absent, 'A', AppColors.danger),
    (AttendanceStatus.late, 'L', AppColors.warning),
    (AttendanceStatus.leave, 'Lv', AppColors.info),
  ];

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (final (status, label, color) in _opts)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 2),
            child: GestureDetector(
              onTap: () => onChanged(status),
              child: CircleAvatar(
                radius: 16,
                backgroundColor: value == status ? color : AppColors.gray100,
                child: Text(label,
                    style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color:
                            value == status ? Colors.white : AppColors.gray500)),
              ),
            ),
          ),
      ],
    );
  }
}
