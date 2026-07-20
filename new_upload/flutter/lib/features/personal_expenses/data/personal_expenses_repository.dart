import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/utils/format.dart';

class PersonalExpenseItem {
  const PersonalExpenseItem({
    required this.title,
    this.amount = 0,
    this.status,
    this.date,
  });
  final String title;
  final num amount;
  final String? status;
  final DateTime? date;

  factory PersonalExpenseItem.fromJson(Map<String, dynamic> j) =>
      PersonalExpenseItem(
        title: (j['title'] ?? j['name'] ?? 'Expense').toString(),
        amount: (j['amount'] as num?) ?? 0,
        status: j['status']?.toString(),
        date: Fmt.parseDate(j['expense_date'] ?? j['date']),
      );
}

class PersonalExpenseSummary {
  const PersonalExpenseSummary({
    this.total = 0,
    this.paid = 0,
    this.due = 0,
    this.items = const [],
  });
  final num total;
  final num paid;
  final num due;
  final List<PersonalExpenseItem> items;

  factory PersonalExpenseSummary.fromJson(Map<String, dynamic> j) {
    final rawItems = j['expenses'] ?? j['items'] ?? j['records'];
    return PersonalExpenseSummary(
      total: (j['total'] ?? j['total_amount'] ?? 0) as num,
      paid: (j['paid'] ?? j['total_paid'] ?? 0) as num,
      due: (j['due'] ?? j['total_due'] ?? j['balance'] ?? 0) as num,
      items: rawItems is List
          ? rawItems
              .whereType<Map>()
              .map((e) =>
                  PersonalExpenseItem.fromJson(Map<String, dynamic>.from(e)))
              .toList()
          : const [],
    );
  }
}

class PersonalExpensesRepository {
  PersonalExpensesRepository(this._dio);
  final Dio _dio;

  Future<PersonalExpenseSummary> studentSummary(String studentId) async {
    try {
      final res = await _dio.get('/personal-expenses/student/$studentId/summary');
      final data = res.data;
      return PersonalExpenseSummary.fromJson(
          data is Map ? Map<String, dynamic>.from(data) : {});
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
