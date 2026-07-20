/// Matches backend `StudentAttendanceSummary` (schemas/phase7.py).
class AttendanceSummary {
  const AttendanceSummary({
    required this.studentId,
    this.studentName,
    this.totalWorkingDays = 0,
    this.daysPresent = 0,
    this.daysAbsent = 0,
    this.daysLate = 0,
    this.daysLeave = 0,
    this.attendancePct = 0,
    this.isLow = false,
  });

  final String studentId;
  final String? studentName;
  final int totalWorkingDays;
  final int daysPresent;
  final int daysAbsent;
  final int daysLate;
  final int daysLeave;
  final double attendancePct;
  final bool isLow;

  factory AttendanceSummary.fromJson(Map<String, dynamic> j) =>
      AttendanceSummary(
        studentId: j['student_id']?.toString() ?? '',
        studentName: j['student_name']?.toString(),
        totalWorkingDays: (j['total_working_days'] as num?)?.toInt() ?? 0,
        daysPresent: (j['days_present'] as num?)?.toInt() ?? 0,
        daysAbsent: (j['days_absent'] as num?)?.toInt() ?? 0,
        daysLate: (j['days_late'] as num?)?.toInt() ?? 0,
        daysLeave: (j['days_leave'] as num?)?.toInt() ?? 0,
        attendancePct: (j['attendance_pct'] as num?)?.toDouble() ?? 0,
        isLow: j['is_low'] == true,
      );
}
