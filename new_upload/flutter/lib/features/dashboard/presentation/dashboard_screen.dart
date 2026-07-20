import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/utils/format.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/skeleton.dart';
import '../../../shared/widgets/stat_card.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/domain/app_role.dart';
import '../../profile/presentation/child_switcher.dart';
import '../application/dashboard_providers.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final async = ref.watch(dashboardProvider);
    final role = auth.role ?? AppRole.admin;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(dashboardProvider),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(dashboardProvider),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const ChildSwitcher(),
            _Greeting(name: auth.user?.displayName ?? 'there', role: role),
            const SizedBox(height: 16),
            async.when(
              loading: () => const Padding(
                  padding: EdgeInsets.only(top: 16), child: SkeletonGrid(count: 6)),
              error: (e, _) => ErrorView(
                message: e.toString(),
                onRetry: () => ref.invalidate(dashboardProvider),
              ),
              data: (m) => _DashboardBody(role: role, data: m),
            ),
          ],
        ),
      ),
    );
  }
}

class _Greeting extends StatelessWidget {
  const _Greeting({required this.name, required this.role});
  final String name;
  final AppRole role;

  @override
  Widget build(BuildContext context) {
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good morning'
        : hour < 17
            ? 'Good afternoon'
            : 'Good evening';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(greeting,
            style: const TextStyle(color: AppColors.gray500, fontSize: 14)),
        Text(name,
            style:
                const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        AppBadge(text: role.label, color: AppColors.primary),
      ],
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({required this.role, required this.data});
  final AppRole role;
  final Map<String, dynamic> data;

  num _n(dynamic v) =>
      v is num ? v : num.tryParse(v?.toString() ?? '') ?? 0;

  @override
  Widget build(BuildContext context) {
    switch (role) {
      case AppRole.superAdmin:
      case AppRole.admin:
        return _admin();
      case AppRole.teacher:
      case AppRole.staff:
        return _teacher();
      case AppRole.parent:
        return _parent();
      case AppRole.student:
        return _student();
    }
  }

  Widget _grid(List<Widget> cards) => GridView.count(
        crossAxisCount: 2,
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 1.5,
        children: cards,
      );

  Widget _admin() {
    return _grid([
      StatCard(
          label: 'Students',
          value: '${_n(data['total_students']).toInt()}',
          icon: Icons.people,
          color: AppColors.primary),
      StatCard(
          label: 'Staff',
          value: '${_n(data['total_staff']).toInt()}',
          icon: Icons.badge,
          color: AppColors.info),
      StatCard(
          label: "Today's attendance",
          value: '${_n(data['attendance_pct_today']).toStringAsFixed(0)}%',
          icon: Icons.check_circle,
          color: AppColors.success),
      StatCard(
          label: 'Pending leaves',
          value: '${_n(data['pending_leave_requests']).toInt()}',
          icon: Icons.event_busy,
          color: AppColors.warning),
      StatCard(
          label: 'Collected (month)',
          value: Fmt.currency(data['total_fee_collected_this_month']),
          icon: Icons.trending_up,
          color: AppColors.success),
      StatCard(
          label: 'Outstanding',
          value: Fmt.currency(data['total_fee_outstanding']),
          icon: Icons.account_balance_wallet,
          color: AppColors.danger),
    ]);
  }

  Widget _teacher() {
    return Column(
      children: [
        _grid([
          StatCard(
              label: 'Homework to review',
              value: '${_n(data['pending_homework_reviews']).toInt()}',
              icon: Icons.rate_review,
              color: AppColors.warning),
          StatCard(
              label: 'Upcoming exams',
              value: '${(data['upcoming_exams'] as List?)?.length ?? 0}',
              icon: Icons.emoji_events,
              color: AppColors.info),
        ]),
        _UpcomingExams(data: data),
      ],
    );
  }

  Widget _student() {
    return Column(
      children: [
        _grid([
          StatCard(
              label: 'Fee outstanding',
              value: Fmt.currency(data['fee_outstanding']),
              icon: Icons.account_balance_wallet,
              color: AppColors.danger),
          StatCard(
              label: 'Homework due',
              value: '${(data['homework_due'] as List?)?.length ?? 0}',
              icon: Icons.description,
              color: AppColors.warning),
        ]),
        _ListSection(
          title: 'Homework due',
          items: (data['homework_due'] as List?) ?? const [],
          titleKey: 'title',
          subKey: 'due_date',
          icon: Icons.description_outlined,
        ),
        _UpcomingExams(data: data),
      ],
    );
  }

  Widget _parent() {
    final children = (data['children'] as List?) ?? const [];
    final attendance = {
      for (final a in (data['attendance_today'] as List? ?? const []))
        if (a is Map) a['student_id']?.toString(): a['status']?.toString(),
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _grid([
          StatCard(
              label: 'Children',
              value: '${children.length}',
              icon: Icons.family_restroom,
              color: AppColors.primary),
          StatCard(
              label: 'Fee due (total)',
              value: Fmt.currency(data['total_fee_due']),
              icon: Icons.account_balance_wallet,
              color: AppColors.danger),
        ]),
        if (children.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Children',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 8),
          for (final c in children.whereType<Map>())
            Container(
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.gray200),
              ),
              child: ListTile(
                leading: const CircleAvatar(child: Icon(Icons.person)),
                title: Text(c['name']?.toString() ?? 'Student'),
                subtitle: Text([
                  if (c['class_name'] != null) c['class_name'],
                  if (c['section_name'] != null) c['section_name'],
                ].whereType().join(' · ')),
                trailing: attendance[c['id']?.toString()] != null
                    ? AppBadge(text: attendance[c['id']?.toString()]!)
                    : null,
              ),
            ),
        ],
        _UpcomingExams(data: data),
      ],
    );
  }
}

class _UpcomingExams extends StatelessWidget {
  const _UpcomingExams({required this.data});
  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final exams = (data['upcoming_exams'] as List?) ?? const [];
    if (exams.isEmpty) return const SizedBox.shrink();
    return _ListSection(
      title: 'Upcoming exams',
      items: exams,
      titleKey: 'name',
      subKey: 'exam_date',
      icon: Icons.emoji_events_outlined,
    );
  }
}

class _ListSection extends StatelessWidget {
  const _ListSection({
    required this.title,
    required this.items,
    required this.titleKey,
    required this.subKey,
    required this.icon,
  });

  final String title;
  final List<dynamic> items;
  final String titleKey;
  final String subKey;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Text(title,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
        const SizedBox(height: 8),
        for (final it in items.whereType<Map>())
          Container(
            margin: const EdgeInsets.only(bottom: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.gray200),
            ),
            child: ListTile(
              dense: true,
              leading: Icon(icon, color: AppColors.primary),
              title: Text(it[titleKey]?.toString() ?? ''),
              subtitle: it[subKey] != null
                  ? Text(Fmt.date(Fmt.parseDate(it[subKey])))
                  : null,
            ),
          ),
      ],
    );
  }
}
