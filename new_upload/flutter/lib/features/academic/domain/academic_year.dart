class AcademicYear {
  const AcademicYear({
    required this.id,
    required this.name,
    this.isCurrent = false,
  });

  final String id;
  final String name;
  final bool isCurrent;

  factory AcademicYear.fromJson(Map<String, dynamic> j) => AcademicYear(
        id: j['id']?.toString() ?? '',
        name: (j['name'] ?? j['year'] ?? '').toString(),
        isCurrent: j['is_current'] == true,
      );
}

class Section {
  const Section({required this.id, required this.name, this.teacherName});

  final String id;
  final String name;
  final String? teacherName;

  factory Section.fromJson(Map<String, dynamic> j) => Section(
        id: j['id']?.toString() ?? '',
        name: (j['name'] ?? j['section_name'] ?? '').toString(),
        teacherName: j['teacher_name']?.toString(),
      );
}

class ClassRoom {
  const ClassRoom({
    required this.id,
    required this.name,
    this.studentCount = 0,
    this.sections = const [],
  });

  final String id;
  final String name;
  final int studentCount;
  final List<Section> sections;

  factory ClassRoom.fromJson(Map<String, dynamic> j) => ClassRoom(
        id: j['id']?.toString() ?? '',
        name: (j['name'] ?? '').toString(),
        studentCount: (j['student_count'] as num?)?.toInt() ?? 0,
        sections: (j['sections'] is List)
            ? (j['sections'] as List)
                .whereType<Map>()
                .map((e) => Section.fromJson(Map<String, dynamic>.from(e)))
                .toList()
            : const [],
      );
}
