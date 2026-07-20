import 'package:flutter/material.dart';
import '../../core/constants.dart';

/// Small status pill. Color is chosen from a status string when [color] is null.
class AppBadge extends StatelessWidget {
  const AppBadge({super.key, required this.text, this.color});

  final String text;
  final Color? color;

  static Color colorForStatus(String status) {
    switch (status.toLowerCase()) {
      case 'present':
      case 'paid':
      case 'approved':
      case 'active':
        return AppColors.success;
      case 'absent':
      case 'overdue':
      case 'rejected':
      case 'inactive':
        return AppColors.danger;
      case 'late':
      case 'pending':
      case 'partial':
        return AppColors.warning;
      case 'excused':
        return AppColors.info;
      default:
        return AppColors.gray500;
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = color ?? colorForStatus(text);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: c.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: TextStyle(color: c, fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }
}
