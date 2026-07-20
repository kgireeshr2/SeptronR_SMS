import '../../../shared/utils/format.dart';

class LeaveType {
  const LeaveType({required this.id, required this.name});
  final String id;
  final String name;

  factory LeaveType.fromJson(Map<String, dynamic> j) => LeaveType(
        id: j['id']?.toString() ?? '',
        name: (j['name'] ?? '').toString(),
      );
}

class LeaveBalance {
  const LeaveBalance({
    required this.leaveTypeName,
    this.entitled = 0,
    this.used = 0,
    this.remaining = 0,
  });

  final String leaveTypeName;
  final double entitled;
  final double used;
  final double remaining;

  factory LeaveBalance.fromJson(Map<String, dynamic> j) => LeaveBalance(
        leaveTypeName: (j['leave_type_name'] ?? 'Leave').toString(),
        entitled: (j['entitled_days'] as num?)?.toDouble() ?? 0,
        used: (j['used_days'] as num?)?.toDouble() ?? 0,
        remaining: (j['remaining_days'] as num?)?.toDouble() ?? 0,
      );
}

class LeaveApplication {
  const LeaveApplication({
    required this.id,
    this.staffName,
    this.leaveTypeName,
    this.fromDate,
    this.toDate,
    this.totalDays,
    this.reason,
    this.status = 'pending',
    this.appliedAt,
  });

  final String id;
  final String? staffName;
  final String? leaveTypeName;
  final DateTime? fromDate;
  final DateTime? toDate;
  final double? totalDays;
  final String? reason;
  final String status;
  final DateTime? appliedAt;

  bool get isPending => status.toLowerCase() == 'pending';

  factory LeaveApplication.fromJson(Map<String, dynamic> j) => LeaveApplication(
        id: j['id']?.toString() ?? '',
        staffName: j['staff_name']?.toString(),
        leaveTypeName: (j['leave_type_name'] ?? j['leave_type'])?.toString(),
        fromDate: Fmt.parseDate(j['from_date'] ?? j['start_date']),
        toDate: Fmt.parseDate(j['to_date'] ?? j['end_date']),
        totalDays: (j['total_days'] as num?)?.toDouble(),
        reason: j['reason']?.toString(),
        status: (j['status'] ?? 'pending').toString(),
        appliedAt: Fmt.parseDate(j['applied_at'] ?? j['created_at']),
      );
}
