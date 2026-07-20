import 'package:flutter/material.dart';

import '../../../core/constants.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/avatar_circle.dart';
import '../domain/staff_member.dart';

class StaffDetailScreen extends StatelessWidget {
  const StaffDetailScreen({super.key, required this.staff});
  final StaffMember staff;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Staff')),
      body: ListView(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 24),
            color: Colors.white,
            child: Column(
              children: [
                AvatarCircle(
                    photoUrl: staff.photoUrl, name: staff.fullName, radius: 44),
                const SizedBox(height: 12),
                Text(staff.fullName,
                    style: const TextStyle(
                        fontSize: 20, fontWeight: FontWeight.w700)),
                if (staff.designationName != null)
                  Text(staff.designationName!,
                      style: const TextStyle(color: AppColors.gray500)),
                const SizedBox(height: 8),
                AppBadge(text: staff.isActive ? 'Active' : 'Inactive'),
              ],
            ),
          ),
          const SizedBox(height: 8),
          _row(Icons.badge_outlined, 'Employee ID', staff.employeeId),
          _row(Icons.apartment_outlined, 'Department', staff.departmentName),
          _row(Icons.email_outlined, 'Email', staff.email),
          _row(Icons.phone_outlined, 'Phone', staff.phone),
          _row(Icons.work_history_outlined, 'Experience',
              staff.experienceYears != null ? '${staff.experienceYears} yrs' : null),
          _row(Icons.event_outlined, 'Joined', staff.dateOfJoining),
        ],
      ),
    );
  }

  Widget _row(IconData icon, String label, String? value) {
    if (value == null || value.isEmpty) return const SizedBox.shrink();
    return ListTile(
      leading: Icon(icon, color: AppColors.primary),
      title: Text(label, style: const TextStyle(color: AppColors.gray500, fontSize: 13)),
      subtitle: Text(value, style: const TextStyle(color: Colors.black, fontSize: 15)),
    );
  }
}
