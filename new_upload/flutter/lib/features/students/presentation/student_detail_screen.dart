import 'package:flutter/material.dart';

import '../../../core/constants.dart';
import '../../../shared/widgets/app_badge.dart';
import '../../../shared/widgets/avatar_circle.dart';
import '../domain/student.dart';

class StudentDetailScreen extends StatelessWidget {
  const StudentDetailScreen({super.key, required this.student});
  final Student student;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Student')),
      body: ListView(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 24),
            color: Colors.white,
            child: Column(
              children: [
                AvatarCircle(
                    photoUrl: student.photoUrl,
                    name: student.fullName,
                    radius: 44),
                const SizedBox(height: 12),
                Text(student.fullName,
                    style: const TextStyle(
                        fontSize: 20, fontWeight: FontWeight.w700)),
                if (student.classLabel.isNotEmpty)
                  Text(student.classLabel,
                      style: const TextStyle(color: AppColors.gray500)),
                if (student.status != null) ...[
                  const SizedBox(height: 8),
                  AppBadge(text: student.status!),
                ],
              ],
            ),
          ),
          const SizedBox(height: 8),
          _row(Icons.confirmation_number_outlined, 'Admission no.',
              student.admissionNumber),
          _row(Icons.wc_outlined, 'Gender', student.gender),
          _row(Icons.family_restroom_outlined, 'Parent', student.parentName),
          _row(Icons.phone_outlined, 'Parent phone', student.parentPhone),
        ],
      ),
    );
  }

  Widget _row(IconData icon, String label, String? value) {
    if (value == null || value.isEmpty) return const SizedBox.shrink();
    return ListTile(
      leading: Icon(icon, color: AppColors.primary),
      title: Text(label,
          style: const TextStyle(color: AppColors.gray500, fontSize: 13)),
      subtitle: Text(value,
          style: const TextStyle(color: Colors.black, fontSize: 15)),
    );
  }
}
