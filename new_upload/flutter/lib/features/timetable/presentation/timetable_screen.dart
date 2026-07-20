import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../academic/application/academic_providers.dart';
import '../../academic/domain/academic_year.dart';
import '../../profile/application/identity_providers.dart';
import '../application/timetable_providers.dart';
import '../domain/timetable_slot.dart';

class TimetableScreen extends ConsumerStatefulWidget {
  const TimetableScreen({super.key});

  @override
  ConsumerState<TimetableScreen> createState() => _TimetableScreenState();
}

class _TimetableScreenState extends ConsumerState<TimetableScreen> {
  ClassRoom? _class;
  Section? _section;

  @override
  Widget build(BuildContext context) {
    // A student sees their own section's timetable directly (no picker).
    final ownSection = ref.watch(currentStudentSectionIdProvider);
    if (ownSection != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Timetable')),
        body: _Body(sectionId: ownSection),
      );
    }

    final classesAsync = ref.watch(classesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Timetable')),
      body: classesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => const _NoAccess(),
        data: (classes) {
          if (classes.isEmpty) return const _NoAccess();
          return Column(
            children: [
              _Selectors(
                classes: classes,
                selectedClass: _class,
                selectedSection: _section,
                onClass: (c) => setState(() {
                  _class = c;
                  _section = null;
                }),
                onSection: (s) => setState(() => _section = s),
              ),
              const Divider(height: 1),
              Expanded(
                child: _section == null
                    ? const EmptyView(
                        message: 'Select a class and section',
                        icon: Icons.calendar_today_outlined)
                    : _Body(sectionId: _section!.id),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _NoAccess extends StatelessWidget {
  const _NoAccess();
  @override
  Widget build(BuildContext context) => const EmptyView(
        icon: Icons.calendar_today_outlined,
        message: 'Your timetable will be shared by your school.',
      );
}

class _Body extends ConsumerWidget {
  const _Body({required this.sectionId});
  final String sectionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(sectionTimetableProvider(sectionId));
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(sectionTimetableProvider(sectionId)),
      ),
      data: (slots) => _TimetableList(slots: slots),
    );
  }
}

class _Selectors extends StatelessWidget {
  const _Selectors({
    required this.classes,
    required this.selectedClass,
    required this.selectedSection,
    required this.onClass,
    required this.onSection,
  });

  final List<ClassRoom> classes;
  final ClassRoom? selectedClass;
  final Section? selectedSection;
  final ValueChanged<ClassRoom?> onClass;
  final ValueChanged<Section?> onSection;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Expanded(
            child: DropdownButtonFormField<ClassRoom>(
              isExpanded: true,
              value: selectedClass,
              decoration:
                  const InputDecoration(labelText: 'Class', isDense: true),
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
              decoration:
                  const InputDecoration(labelText: 'Section', isDense: true),
              items: [
                for (final s in selectedClass?.sections ?? const [])
                  DropdownMenuItem(value: s, child: Text(s.name)),
              ],
              onChanged: onSection,
            ),
          ),
        ],
      ),
    );
  }
}

class _TimetableList extends StatelessWidget {
  const _TimetableList({required this.slots});
  final List<TimetableSlot> slots;

  @override
  Widget build(BuildContext context) {
    if (slots.isEmpty) {
      return const EmptyView(
          message: 'No timetable set for this section',
          icon: Icons.calendar_today_outlined);
    }
    final byDay = <String, List<TimetableSlot>>{};
    for (final s in slots) {
      byDay.putIfAbsent(s.dayLabel, () => []).add(s);
    }
    final days = byDay.keys.toList()
      ..sort((a, b) =>
          byDay[a]!.first.daySort.compareTo(byDay[b]!.first.daySort));

    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        for (final day in days) ...[
          Padding(
            padding: const EdgeInsets.fromLTRB(4, 12, 4, 6),
            child: Text(day,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w700)),
          ),
          ...(byDay[day]!
                ..sort((a, b) =>
                    (a.periodNumber ?? 0).compareTo(b.periodNumber ?? 0)))
              .map((s) => _SlotTile(slot: s)),
        ],
      ],
    );
  }
}

class _SlotTile extends StatelessWidget {
  const _SlotTile({required this.slot});
  final TimetableSlot slot;

  @override
  Widget build(BuildContext context) {
    final time =
        [slot.startTime, slot.endTime].whereType<String>().join(' – ');
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.gray200),
      ),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppColors.primaryLight.withOpacity(0.15),
          child: Text('${slot.periodNumber ?? '-'}',
              style: const TextStyle(
                  color: AppColors.primary, fontWeight: FontWeight.w700)),
        ),
        title: Text(slot.subjectName ?? 'Period ${slot.periodNumber ?? ''}'),
        subtitle: Text([
          if (slot.staffName != null) slot.staffName,
          if (time.isNotEmpty) time,
        ].whereType<String>().join(' · ')),
      ),
    );
  }
}
