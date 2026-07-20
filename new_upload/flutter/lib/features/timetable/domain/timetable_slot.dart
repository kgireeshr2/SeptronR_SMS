class TimetableSlot {
  const TimetableSlot({
    required this.id,
    this.dayOfWeek,
    this.dayName,
    this.periodNumber,
    this.startTime,
    this.endTime,
    this.subjectName,
    this.staffName,
  });

  final String id;
  final int? dayOfWeek;
  final String? dayName;
  final int? periodNumber;
  final String? startTime;
  final String? endTime;
  final String? subjectName;
  final String? staffName;

  static const _days = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
  ];

  /// A stable day label for grouping, derived from name or index.
  String get dayLabel {
    if (dayName != null && dayName!.isNotEmpty) return dayName!;
    if (dayOfWeek != null && dayOfWeek! >= 1 && dayOfWeek! <= 7) {
      return _days[dayOfWeek! - 1];
    }
    return 'Other';
  }

  int get daySort => dayOfWeek ?? (_days.indexOf(dayLabel) + 1).clamp(1, 8);

  factory TimetableSlot.fromJson(Map<String, dynamic> j) => TimetableSlot(
        id: j['id']?.toString() ?? '',
        dayOfWeek: (j['day_of_week'] as num?)?.toInt(),
        dayName: j['day_name']?.toString(),
        periodNumber: (j['period_number'] as num?)?.toInt(),
        startTime: j['start_time']?.toString(),
        endTime: j['end_time']?.toString(),
        subjectName: j['subject_name']?.toString(),
        staffName: j['staff_name']?.toString(),
      );
}
