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
import '../data/personal_expenses_repository.dart';

final _personalExpensesRepoProvider =
    Provider<PersonalExpensesRepository>((ref) {
  return PersonalExpensesRepository(ref.watch(dioProvider));
});

final _personalExpensesProvider =
    FutureProvider.autoDispose<PersonalExpenseSummary?>((ref) async {
  final studentId = ref.watch(currentStudentIdProvider);
  if (studentId == null) return null;
  return ref.watch(_personalExpensesRepoProvider).studentSummary(studentId);
});

class PersonalExpensesScreen extends ConsumerWidget {
  const PersonalExpensesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_personalExpensesProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Expenses')),
      body: Column(
        children: [
          const ChildSwitcher(),
          Expanded(
            child: async.when(
              loading: () => const LoadingView(),
              error: (e, _) => ErrorView(
                message: e.toString(),
                onRetry: () => ref.invalidate(_personalExpensesProvider),
              ),
              data: (s) {
                if (s == null) {
                  return const EmptyView(
                      message:
                          'Expenses appear here once a student profile is linked.',
                      icon: Icons.shopping_bag_outlined);
                }
                return RefreshIndicator(
                  onRefresh: () async =>
                      ref.invalidate(_personalExpensesProvider),
                  child: ListView(
                    padding: const EdgeInsets.all(12),
                    children: [
                      Row(
                        children: [
                          Expanded(
                              child: _stat('Total', s.total, AppColors.primary)),
                          const SizedBox(width: 8),
                          Expanded(
                              child: _stat('Paid', s.paid, AppColors.success)),
                          const SizedBox(width: 8),
                          Expanded(
                              child: _stat('Due', s.due, AppColors.danger)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (s.items.isEmpty)
                        const Padding(
                          padding: EdgeInsets.only(top: 40),
                          child: EmptyView(message: 'No expenses'),
                        )
                      else
                        for (final it in s.items)
                          Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: AppColors.gray200),
                            ),
                            child: ListTile(
                              title: Text(it.title),
                              subtitle: it.date != null
                                  ? Text(Fmt.date(it.date))
                                  : null,
                              trailing: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text(Fmt.currency(it.amount),
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w700)),
                                  if (it.status != null)
                                    AppBadge(text: it.status!),
                                ],
                              ),
                            ),
                          ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _stat(String label, num value, Color color) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.gray200),
        ),
        child: Column(
          children: [
            Text(Fmt.currency(value),
                style: TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w800, color: color)),
            const SizedBox(height: 2),
            Text(label,
                style: const TextStyle(
                    color: AppColors.gray500, fontSize: 12)),
          ],
        ),
      );
}
