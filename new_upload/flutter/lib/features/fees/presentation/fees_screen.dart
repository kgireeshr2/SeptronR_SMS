import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/domain/app_role.dart';
import '../../profile/presentation/child_switcher.dart';
import '../application/fees_providers.dart';
import '../domain/fee_invoice.dart';

class FeesScreen extends ConsumerWidget {
  const FeesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final role = ref.watch(roleProvider);
    final isAdmin = role == AppRole.admin || role == AppRole.superAdmin;
    return Scaffold(
      appBar: AppBar(title: const Text('Fees')),
      body: isAdmin ? const _AdminFees() : const _StudentFees(),
    );
  }
}

// ─── Parent/Student: statement ───────────────────────────────────────────────
class _StudentFees extends ConsumerWidget {
  const _StudentFees();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(feeStatementProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(feeStatementProvider),
      ),
      data: (st) {
        if (st == null) {
          return Column(children: const [
            ChildSwitcher(),
            Expanded(
              child: EmptyView(
                  message:
                      'Fee details will appear here once your profile is linked.',
                  icon: Icons.receipt_long_outlined),
            ),
          ]);
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(feeStatementProvider),
          child: ListView(
            padding: const EdgeInsets.all(12),
            children: [
              const ChildSwitcher(),
              const SizedBox(height: 8),
              _TotalsCard(
                  paid: st.totalPaid, due: st.totalDue, total: st.totalAmount),
              const SizedBox(height: 8),
              if (st.invoices.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 40),
                  child: EmptyView(message: 'No invoices'),
                )
              else
                for (final inv in st.invoices)
                  _InvoiceCard(inv: inv, onTap: () => _detail(context, inv)),
            ],
          ),
        );
      },
    );
  }
}

class _AdminFees extends ConsumerWidget {
  const _AdminFees();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final invoices = ref.watch(adminInvoicesProvider);
    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(adminInvoicesProvider);
        ref.invalidate(monthlyCollectionProvider);
      },
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          const _CollectionSummaryCard(),
          const _DefaultersTile(),
          invoices.when(
            loading: () => const Padding(
                padding: EdgeInsets.only(top: 60), child: LoadingView()),
            error: (e, _) => ErrorView(
              message: e.toString(),
              onRetry: () => ref.invalidate(adminInvoicesProvider),
            ),
            data: (items) {
              if (items.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.only(top: 40),
                  child: EmptyView(message: 'No invoices'),
                );
              }
              return Column(
                children: [
                  for (final inv in items)
                    _InvoiceCard(inv: inv, onTap: () => _detail(context, inv)),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

void _detail(BuildContext context, FeeInvoice inv) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.6,
      maxChildSize: 0.92,
      builder: (_, controller) => ListView(
        controller: controller,
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(inv.invoiceNumber ?? 'Invoice',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w700)),
              ),
              AppBadge(text: inv.status),
            ],
          ),
          if (inv.studentName != null) ...[
            const SizedBox(height: 4),
            Text(inv.studentName!,
                style: const TextStyle(color: AppColors.gray500)),
          ],
          const Divider(height: 24),
          if (inv.items.isNotEmpty) ...[
            const Text('Items', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            for (final it in inv.items)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(child: Text(it.name)),
                    Text(Fmt.currency(it.amount)),
                  ],
                ),
              ),
            const Divider(height: 24),
          ],
          _amountRow('Total', inv.totalAmount),
          _amountRow('Paid', inv.paidAmount, color: AppColors.success),
          _amountRow('Outstanding', inv.outstanding,
              color: inv.outstanding > 0 ? AppColors.danger : AppColors.gray700,
              bold: true),
          if (inv.dueDate != null) ...[
            const SizedBox(height: 12),
            Text('Due ${Fmt.date(inv.dueDate)}',
                style: const TextStyle(color: AppColors.gray500)),
          ],
        ],
      ),
    ),
  );
}

Widget _amountRow(String label, num value,
    {Color color = AppColors.gray700, bool bold = false}) {
  return Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style:
                TextStyle(fontWeight: bold ? FontWeight.w700 : FontWeight.w400)),
        Text(Fmt.currency(value),
            style: TextStyle(
                color: color,
                fontWeight: bold ? FontWeight.w700 : FontWeight.w500)),
      ],
    ),
  );
}

class _TotalsCard extends StatelessWidget {
  const _TotalsCard(
      {required this.paid, required this.due, required this.total});
  final num paid;
  final num due;
  final num total;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
            colors: [AppColors.primary, AppColors.primaryLight]),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Text(Fmt.currency(due),
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 30,
                  fontWeight: FontWeight.w800)),
          const Text('Outstanding',
              style: TextStyle(color: Colors.white70)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _mini('Paid', paid),
              Container(width: 1, height: 28, color: Colors.white24),
              _mini('Total', total),
            ],
          ),
        ],
      ),
    );
  }

  Widget _mini(String label, num v) => Column(
        children: [
          Text(Fmt.currency(v),
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w700)),
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
        ],
      );
}

class _InvoiceCard extends StatelessWidget {
  const _InvoiceCard({required this.inv, required this.onTap});
  final FeeInvoice inv;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.gray200),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        title: Text(inv.invoiceNumber ?? inv.studentName ?? 'Invoice',
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Text(
            'Outstanding ${Fmt.currency(inv.outstanding)}'
            '${inv.dueDate != null ? ' · due ${Fmt.date(inv.dueDate)}' : ''}',
            style: const TextStyle(color: AppColors.gray500),
          ),
        ),
        trailing: AppBadge(text: inv.status),
        onTap: onTap,
      ),
    );
  }
}

class _DefaultersTile extends ConsumerWidget {
  const _DefaultersTile();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(defaultersProvider);
    return async.maybeWhen(
      data: (list) {
        if (list.isEmpty) return const SizedBox.shrink();
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.gray200),
          ),
          child: ExpansionTile(
            shape: const Border(),
            leading: const Icon(Icons.warning_amber_rounded,
                color: AppColors.danger),
            title: Text('Defaulters (${list.length})',
                style: const TextStyle(fontWeight: FontWeight.w700)),
            children: [
              for (final d in list)
                ListTile(
                  dense: true,
                  title: Text(d.studentName),
                  subtitle: Text(
                      '${d.invoiceNumber ?? ''} · ${d.daysOverdue}d overdue'),
                  trailing: Text(Fmt.currency(d.balanceAmount),
                      style: const TextStyle(
                          color: AppColors.danger,
                          fontWeight: FontWeight.w700)),
                ),
            ],
          ),
        );
      },
      orElse: () => const SizedBox.shrink(),
    );
  }
}

class _CollectionSummaryCard extends ConsumerWidget {
  const _CollectionSummaryCard();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(monthlyCollectionProvider);
    return async.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (m) {
        final collected = m['total_collected'] ??
            m['collected'] ??
            m['total_paid'] ??
            m['amount'];
        final pending =
            m['total_pending'] ?? m['pending'] ?? m['total_due'] ?? m['due'];
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
                colors: [AppColors.primary, AppColors.primaryLight]),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            children: [
              Expanded(child: _metric('Collected', Fmt.currency(collected ?? 0))),
              Container(width: 1, height: 40, color: Colors.white24),
              Expanded(child: _metric('Pending', Fmt.currency(pending ?? 0))),
            ],
          ),
        );
      },
    );
  }

  Widget _metric(String label, String value) => Column(
        children: [
          Text(value,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w700)),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 13)),
        ],
      );
}
