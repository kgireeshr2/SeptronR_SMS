import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../core/providers.dart';
import '../../academic/application/academic_providers.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../data/reports_repository.dart';

final _reportsRepoProvider = Provider<ReportsRepository>((ref) {
  return ReportsRepository(ref.watch(dioProvider));
});

final _availableReportsProvider =
    FutureProvider.autoDispose<List<ReportInfo>>((ref) {
  return ref.watch(_reportsRepoProvider).available();
});

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_availableReportsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Reports')),
      body: async.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(_availableReportsProvider),
        ),
        data: (reports) {
          if (reports.isEmpty) {
            return const EmptyView(message: 'No reports available');
          }
          final groups = <String, List<ReportInfo>>{};
          for (final r in reports) {
            groups.putIfAbsent(r.group, () => []).add(r);
          }
          return ListView(
            padding: const EdgeInsets.all(12),
            children: [
              for (final entry in groups.entries) ...[
                Padding(
                  padding: const EdgeInsets.fromLTRB(4, 12, 4, 6),
                  child: Text(entry.key.toUpperCase(),
                      style: const TextStyle(
                          color: AppColors.gray500,
                          fontWeight: FontWeight.w700,
                          fontSize: 12,
                          letterSpacing: 0.5)),
                ),
                for (final r in entry.value)
                  Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.gray200),
                    ),
                    child: ListTile(
                      leading: const Icon(Icons.bar_chart_outlined,
                          color: AppColors.primary),
                      title: Text(r.title),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(
                          builder: (_) => _ReportResultScreen(report: r))),
                    ),
                  ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _ReportResultScreen extends ConsumerWidget {
  const _ReportResultScreen({required this.report});
  final ReportInfo report;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rowsAsync = ref.watch(_reportRowsProvider(report.id));
    return Scaffold(
      appBar: AppBar(title: Text(report.title)),
      body: rowsAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(_reportRowsProvider(report.id)),
        ),
        data: (rows) {
          if (rows.isEmpty) {
            return const EmptyView(message: 'No data for this report');
          }
          final columns = rows.first.keys.toList();
          return SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SingleChildScrollView(
              child: DataTable(
                columns: [
                  for (final c in columns)
                    DataColumn(label: Text(_pretty(c))),
                ],
                rows: [
                  for (final r in rows)
                    DataRow(cells: [
                      for (final c in columns)
                        DataCell(Text('${r[c] ?? ''}')),
                    ]),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  String _pretty(String key) => key
      .split('_')
      .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
      .join(' ');
}

final _reportRowsProvider = FutureProvider.family
    .autoDispose<List<Map<String, dynamic>>, String>((ref, reportId) async {
  final year = await ref.watch(currentYearProvider.future);
  return ref
      .watch(_reportsRepoProvider)
      .run(reportId, yearId: year?.id);
});
