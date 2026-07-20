import '../../../shared/utils/format.dart';

class Book {
  const Book({
    required this.id,
    required this.title,
    this.author,
    this.isbn,
    this.categoryName,
    this.availableCopies,
    this.totalCopies,
  });

  final String id;
  final String title;
  final String? author;
  final String? isbn;
  final String? categoryName;
  final int? availableCopies;
  final int? totalCopies;

  bool get isAvailable => (availableCopies ?? 0) > 0;

  factory Book.fromJson(Map<String, dynamic> j) => Book(
        id: j['id']?.toString() ?? '',
        title: (j['title'] ?? j['name'] ?? '').toString(),
        author: j['author']?.toString(),
        isbn: j['isbn']?.toString(),
        categoryName: (j['category_name'] ?? j['category'])?.toString(),
        availableCopies: (j['available_copies'] as num?)?.toInt(),
        totalCopies: (j['total_copies'] as num?)?.toInt(),
      );
}

class BookIssue {
  const BookIssue({
    required this.id,
    this.bookTitle,
    this.issueDate,
    this.dueDate,
    this.returnDate,
    this.status,
    this.fine,
  });

  final String id;
  final String? bookTitle;
  final DateTime? issueDate;
  final DateTime? dueDate;
  final DateTime? returnDate;
  final String? status;
  final num? fine;

  bool get isOverdue =>
      returnDate == null && dueDate != null && dueDate!.isBefore(DateTime.now());

  factory BookIssue.fromJson(Map<String, dynamic> j) => BookIssue(
        id: j['id']?.toString() ?? '',
        bookTitle: (j['book_title'] ?? j['title'] ?? j['book_name'])?.toString(),
        issueDate: Fmt.parseDate(j['issue_date']),
        dueDate: Fmt.parseDate(j['due_date']),
        returnDate: Fmt.parseDate(j['return_date']),
        status: j['status']?.toString(),
        fine: j['fine_amount'] as num? ?? j['fine'] as num?,
      );
}
