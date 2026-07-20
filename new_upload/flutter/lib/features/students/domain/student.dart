class Student {
  const Student({
    required this.id,
    required this.fullName,
    this.admissionNumber,
    this.className,
    this.sectionName,
    this.classId,
    this.sectionId,
    this.gender,
    this.parentName,
    this.parentPhone,
    this.photoUrl,
    this.status,
    this.userId,
  });

  final String id;
  final String fullName;
  final String? admissionNumber;
  final String? className;
  final String? sectionName;
  final String? classId;
  final String? sectionId;
  final String? gender;
  final String? parentName;
  final String? parentPhone;
  final String? photoUrl;
  final String? status;
  final String? userId;

  String get classLabel => [
        if (className != null) className,
        if (sectionName != null) sectionName,
      ].whereType<String>().join(' · ');

  factory Student.fromJson(Map<String, dynamic> j) => Student(
        id: j['id']?.toString() ?? '',
        fullName: (j['full_name'] ??
                '${j['first_name'] ?? ''} ${j['last_name'] ?? ''}')
            .toString()
            .trim(),
        admissionNumber: j['admission_number']?.toString(),
        className: j['class_name']?.toString(),
        sectionName: j['section_name']?.toString(),
        classId: j['class_id']?.toString(),
        sectionId: j['section_id']?.toString(),
        gender: j['gender']?.toString(),
        parentName: j['parent_name']?.toString(),
        parentPhone: j['parent_phone']?.toString(),
        photoUrl: (j['photo_url'] ?? j['photo'])?.toString(),
        status: j['status']?.toString(),
        userId: j['user_id']?.toString(),
      );
}
