import '../../../shared/utils/format.dart';

class FeeItem {
  const FeeItem({required this.name, required this.amount, this.paidAmount = 0});

  final String name;
  final num amount;
  final num paidAmount;

  factory FeeItem.fromJson(Map<String, dynamic> j) => FeeItem(
        name: (j['fee_name'] ?? j['fee_category_name'] ?? j['name'] ?? 'Fee')
            .toString(),
        amount: _num(j['amount']),
        paidAmount: _num(j['paid_amount']),
      );
}

class FeeInvoice {
  const FeeInvoice({
    required this.id,
    this.invoiceNumber,
    this.studentId,
    this.studentName,
    this.totalAmount = 0,
    this.paidAmount = 0,
    this.dueAmount,
    this.dueDate,
    this.status = 'pending',
    this.items = const [],
  });

  final String id;
  final String? invoiceNumber;
  final String? studentId;
  final String? studentName;
  final num totalAmount;
  final num paidAmount;
  final num? dueAmount;
  final DateTime? dueDate;
  final String status;
  final List<FeeItem> items;

  num get outstanding => dueAmount ?? (totalAmount - paidAmount);

  factory FeeInvoice.fromJson(Map<String, dynamic> j) => FeeInvoice(
        id: j['id']?.toString() ?? '',
        invoiceNumber: j['invoice_number']?.toString(),
        studentId: j['student_id']?.toString(),
        studentName: j['student_name']?.toString(),
        totalAmount: _num(j['total_amount']),
        paidAmount: _num(j['paid_amount']),
        dueAmount: j['due_amount'] == null ? null : _num(j['due_amount']),
        dueDate: Fmt.parseDate(j['due_date']),
        status: (j['status'] ?? 'pending').toString(),
        items: (j['items'] is List)
            ? (j['items'] as List)
                .whereType<Map>()
                .map((e) => FeeItem.fromJson(Map<String, dynamic>.from(e)))
                .toList()
            : const [],
      );
}

/// `StudentFeeStatement` — totals + invoices for one student.
class FeeStatement {
  const FeeStatement({
    required this.studentId,
    this.studentName,
    this.totalAmount = 0,
    this.totalPaid = 0,
    this.totalDue = 0,
    this.invoices = const [],
  });

  final String studentId;
  final String? studentName;
  final num totalAmount;
  final num totalPaid;
  final num totalDue;
  final List<FeeInvoice> invoices;

  factory FeeStatement.fromJson(Map<String, dynamic> j) => FeeStatement(
        studentId: j['student_id']?.toString() ?? '',
        studentName: j['student_name']?.toString(),
        totalAmount: _num(j['total_amount']),
        totalPaid: _num(j['total_paid']),
        totalDue: _num(j['total_due']),
        invoices: (j['invoices'] is List)
            ? (j['invoices'] as List)
                .whereType<Map>()
                .map((e) => FeeInvoice.fromJson(Map<String, dynamic>.from(e)))
                .toList()
            : const [],
      );
}

/// `DefaulterEntry` — an overdue invoice.
class Defaulter {
  const Defaulter({
    required this.studentName,
    this.invoiceNumber,
    this.balanceAmount = 0,
    this.daysOverdue = 0,
  });

  final String studentName;
  final String? invoiceNumber;
  final num balanceAmount;
  final int daysOverdue;

  factory Defaulter.fromJson(Map<String, dynamic> j) => Defaulter(
        studentName: (j['student_name'] ?? 'Student').toString(),
        invoiceNumber: j['invoice_number']?.toString(),
        balanceAmount: _num(j['balance_amount']),
        daysOverdue: (j['days_overdue'] as num?)?.toInt() ?? 0,
      );
}

num _num(dynamic v) {
  if (v == null) return 0;
  if (v is num) return v;
  return num.tryParse(v.toString()) ?? 0;
}
