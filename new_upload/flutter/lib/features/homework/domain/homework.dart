import '../../../shared/utils/format.dart';

class Homework {
  const Homework({
    required this.id,
    required this.title,
    this.description,
    this.subjectId,
    this.subjectName,
    this.classId,
    this.className,
    this.dueDate,
    this.assignedByName,
    this.createdAt,
  });

  final String id;
  final String title;
  final String? description;
  final String? subjectId;
  final String? subjectName;
  final String? classId;
  final String? className;
  final DateTime? dueDate;
  final String? assignedByName;
  final DateTime? createdAt;

  bool get isOverdue =>
      dueDate != null && dueDate!.isBefore(DateTime.now());

  factory Homework.fromJson(Map<String, dynamic> j) => Homework(
        id: j['id']?.toString() ?? '',
        title: j['title']?.toString() ?? '',
        description: j['description']?.toString(),
        subjectId: j['subject_id']?.toString(),
        subjectName: j['subject_name']?.toString(),
        classId: j['class_id']?.toString(),
        className: j['class_name']?.toString(),
        dueDate: Fmt.parseDate(j['due_date']),
        assignedByName: j['assigned_by_name']?.toString(),
        createdAt: Fmt.parseDate(j['created_at']),
      );
}

/// `HomeworkSubmissionResponse`.
class HomeworkSubmission {
  const HomeworkSubmission({
    required this.id,
    this.studentId,
    this.studentName,
    this.content,
    this.marksGiven,
    this.remarks,
    this.submittedAt,
  });

  final String id;
  final String? studentId;
  final String? studentName;
  final String? content;
  final int? marksGiven;
  final String? remarks;
  final DateTime? submittedAt;

  bool get isGraded => marksGiven != null;

  factory HomeworkSubmission.fromJson(Map<String, dynamic> j) =>
      HomeworkSubmission(
        id: j['id']?.toString() ?? '',
        studentId: j['student_id']?.toString(),
        studentName: j['student_name']?.toString(),
        content: j['content']?.toString(),
        marksGiven: (j['marks_given'] as num?)?.toInt(),
        remarks: j['remarks']?.toString(),
        submittedAt: Fmt.parseDate(j['submitted_at']),
      );
}
