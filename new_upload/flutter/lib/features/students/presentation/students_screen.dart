import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/widgets/avatar_circle.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/skeleton.dart';
import '../../../shared/widgets/search_field.dart';
import '../application/students_providers.dart';
import 'student_detail_screen.dart';

class StudentsScreen extends ConsumerStatefulWidget {
  const StudentsScreen({super.key});

  @override
  ConsumerState<StudentsScreen> createState() => _StudentsScreenState();
}

class _StudentsScreenState extends ConsumerState<StudentsScreen> {
  String _search = '';

  @override
  Widget build(BuildContext context) {
    final query = StudentQuery(search: _search.isEmpty ? null : _search);
    final async = ref.watch(studentsProvider(query));

    return Scaffold(
      appBar: AppBar(title: const Text('Students')),
      body: Column(
        children: [
          SearchField(
            hint: 'Search students…',
            onChanged: (v) => setState(() => _search = v),
          ),
          Expanded(
            child: async.when(
              loading: () => const SkeletonList(),
              error: (e, _) => ErrorView(
                message: e.toString(),
                onRetry: () => ref.invalidate(studentsProvider(query)),
              ),
              data: (items) {
                if (items.isEmpty) {
                  return const EmptyView(message: 'No students found');
                }
                return RefreshIndicator(
                  onRefresh: () async =>
                      ref.invalidate(studentsProvider(query)),
                  child: ListView.separated(
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (_, i) {
                      final s = items[i];
                      return ListTile(
                        leading: AvatarCircle(
                            photoUrl: s.photoUrl, name: s.fullName),
                        title: Text(s.fullName),
                        subtitle: Text([
                          if (s.admissionNumber != null) s.admissionNumber,
                          if (s.classLabel.isNotEmpty) s.classLabel,
                        ].whereType<String>().join(' · ')),
                        trailing: const Icon(Icons.chevron_right,
                            color: AppColors.gray500),
                        onTap: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => StudentDetailScreen(student: s),
                          ),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
