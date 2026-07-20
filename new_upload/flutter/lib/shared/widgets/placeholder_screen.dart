import 'package:flutter/material.dart';
import '../../core/constants.dart';

/// Temporary screen for modules not yet implemented. Replaced incrementally
/// as later phases build out each feature.
class PlaceholderScreen extends StatelessWidget {
  const PlaceholderScreen({super.key, required this.title, this.icon});

  final String title;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon ?? Icons.construction_outlined,
                size: 64, color: AppColors.gray200),
            const SizedBox(height: 12),
            Text('$title — coming soon',
                style: const TextStyle(color: AppColors.gray500, fontSize: 16)),
          ],
        ),
      ),
    );
  }
}
