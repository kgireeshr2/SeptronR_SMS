import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/widgets/avatar_circle.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/skeleton.dart';
import '../../../shared/widgets/search_field.dart';
import '../application/staff_providers.dart';
import 'staff_detail_screen.dart';

class StaffScreen extends ConsumerStatefulWidget {
  const StaffScreen({super.key});

  @override
  ConsumerState<StaffScreen> createState() => _StaffScreenState();
}

class _StaffScreenState extends ConsumerState<StaffScreen> {
  String _search = '';

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(staffListProvider(_search));
    return Scaffold(
      appBar: AppBar(title: const Text('Staff')),
      body: Column(
        children: [
          SearchField(
            hint: 'Search staff…',
            onChanged: (v) => setState(() => _search = v),
          ),
          Expanded(
            child: async.when(
              loading: () => const SkeletonList(),
              error: (e, _) => ErrorView(
                message: e.toString(),
                onRetry: () => ref.invalidate(staffListProvider(_search)),
              ),
              data: (items) {
                if (items.isEmpty) {
                  return const EmptyView(message: 'No staff found');
                }
                return RefreshIndicator(
                  onRefresh: () async =>
                      ref.invalidate(staffListProvider(_search)),
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
                          if (s.designationName != null) s.designationName,
                          if (s.departmentName != null) s.departmentName,
                        ].whereType<String>().join(' · ')),
                        trailing: const Icon(Icons.chevron_right,
                            color: AppColors.gray500),
                        onTap: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => StaffDetailScreen(staff: s),
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
