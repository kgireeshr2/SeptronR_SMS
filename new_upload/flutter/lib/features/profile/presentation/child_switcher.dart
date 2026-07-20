import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/widgets/avatar_circle.dart';
import '../application/identity_providers.dart';
import '../domain/child_ref.dart';

/// A compact banner letting a parent switch the active child. Renders nothing
/// for non-parents or single-child accounts. Place at the top of parent-facing
/// screen bodies; switching refreshes any screen that reads currentStudentId.
class ChildSwitcher extends ConsumerWidget {
  const ChildSwitcher({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final children = ref.watch(childrenProvider).valueOrNull ?? const [];
    if (children.length < 2) return const SizedBox.shrink();
    final active = ref.watch(activeChildProvider);
    if (active == null) return const SizedBox.shrink();

    return Material(
      color: AppColors.primaryLight.withOpacity(0.10),
      child: InkWell(
        onTap: () => _pick(context, ref, children, active),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            children: [
              AvatarCircle(name: active.name, radius: 16),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(active.name,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    if (active.classLabel.isNotEmpty)
                      Text(active.classLabel,
                          style: const TextStyle(
                              color: AppColors.gray500, fontSize: 12)),
                  ],
                ),
              ),
              const Icon(Icons.unfold_more, color: AppColors.primary),
            ],
          ),
        ),
      ),
    );
  }

  void _pick(BuildContext context, WidgetRef ref, List<ChildRef> children,
      ChildRef active) {
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.all(8),
              child: Text('Select child',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            ),
            for (final c in children)
              ListTile(
                leading: AvatarCircle(name: c.name, radius: 18),
                title: Text(c.name),
                subtitle:
                    c.classLabel.isNotEmpty ? Text(c.classLabel) : null,
                trailing: c.id == active.id
                    ? const Icon(Icons.check_circle, color: AppColors.primary)
                    : null,
                onTap: () {
                  ref.read(activeChildIdProvider.notifier).select(c.id);
                  Navigator.pop(context);
                },
              ),
          ],
        ),
      ),
    );
  }
}
