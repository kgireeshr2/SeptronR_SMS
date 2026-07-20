/// A child linked to a parent, as returned by `GET /dashboard/parent`.
class ChildRef {
  const ChildRef({
    required this.id,
    required this.name,
    this.admissionNumber,
    this.className,
    this.sectionName,
  });

  final String id;
  final String name;
  final String? admissionNumber;
  final String? className;
  final String? sectionName;

  String get classLabel => [
        if (className != null) className,
        if (sectionName != null) sectionName,
      ].whereType<String>().join(' · ');

  factory ChildRef.fromJson(Map<String, dynamic> j) => ChildRef(
        id: j['id']?.toString() ?? '',
        name: (j['name'] ?? '').toString(),
        admissionNumber: j['admission_number']?.toString(),
        className: j['class_name']?.toString(),
        sectionName: j['section_name']?.toString(),
      );
}
