import '../../../shared/utils/format.dart';

class Exam {
  const Exam({
    required this.id,
    required this.name,
    this.examTypeName,
    this.date,
    this.className,
    this.subjectName,
    this.status,
  });

  final String id;
  final String name;
  final String? examTypeName;
  final DateTime? date;
  final String? className;
  final String? subjectName;
  final String? status;

  factory Exam.fromJson(Map<String, dynamic> j) => Exam(
        id: j['id']?.toString() ?? '',
        name: (j['name'] ?? '').toString(),
        examTypeName: j['exam_type_name']?.toString(),
        date: Fmt.parseDate(j['exam_date'] ?? j['start_date']),
        className: j['class_name']?.toString(),
        subjectName: j['subject_name']?.toString(),
        status: j['status']?.toString(),
      );
}

/// `ExamMarkResponse` — one student's mark in an exam (subject).
class ExamMark {
  const ExamMark({
    required this.studentId,
    required this.studentName,
    this.admissionNumber,
    this.marksObtained,
    this.fullMarks,
    this.grade,
    this.percentage,
  });

  final String studentId;
  final String studentName;
  final String? admissionNumber;
  final double? marksObtained;
  final num? fullMarks;
  final String? grade;
  final num? percentage;

  factory ExamMark.fromJson(Map<String, dynamic> j) => ExamMark(
        studentId: j['student_id']?.toString() ?? '',
        studentName: (j['student_name'] ?? '').toString(),
        admissionNumber: j['admission_number']?.toString(),
        marksObtained: (j['marks_obtained'] as num?)?.toDouble(),
        fullMarks: j['full_marks'] as num?,
        grade: j['grade']?.toString(),
        percentage: j['percentage'] as num?,
      );
}
