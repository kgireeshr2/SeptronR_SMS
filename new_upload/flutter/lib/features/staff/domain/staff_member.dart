class StaffMember {
  const StaffMember({
    required this.id,
    required this.fullName,
    this.employeeId,
    this.designationName,
    this.departmentName,
    this.email,
    this.phone,
    this.photoUrl,
    this.isActive = true,
    this.experienceYears,
    this.dateOfJoining,
  });

  final String id;
  final String fullName;
  final String? employeeId;
  final String? designationName;
  final String? departmentName;
  final String? email;
  final String? phone;
  final String? photoUrl;
  final bool isActive;
  final num? experienceYears;
  final String? dateOfJoining;

  factory StaffMember.fromJson(Map<String, dynamic> j) => StaffMember(
        id: j['id']?.toString() ?? '',
        fullName: (j['full_name'] ??
                '${j['first_name'] ?? ''} ${j['last_name'] ?? ''}')
            .toString()
            .trim(),
        employeeId: j['employee_id']?.toString(),
        designationName: j['designation_name']?.toString(),
        departmentName: j['department_name']?.toString(),
        email: j['email']?.toString(),
        phone: j['phone']?.toString(),
        photoUrl: (j['photo_url'] ?? j['photo'])?.toString(),
        isActive: j['is_active'] != false,
        experienceYears: j['experience_years'] as num?,
        dateOfJoining: j['date_of_joining']?.toString(),
      );
}
