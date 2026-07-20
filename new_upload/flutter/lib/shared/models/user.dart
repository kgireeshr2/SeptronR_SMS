/// Backend user (snake_case, UUID ids). `permissions` arrives either as a
/// space-separated string (`/auth/me`) or a list (`/auth/login`) — normalized
/// here to `List<String>`.
class User {
  const User({
    required this.id,
    required this.username,
    required this.email,
    required this.isSuperAdmin,
    required this.permissions,
    this.fullName,
    this.phone,
    this.isActive = true,
    this.isVerified,
    this.avatarUrl,
    this.schoolId,
  });

  final String id;
  final String username;
  final String email;
  final bool isSuperAdmin;
  final List<String> permissions;
  final String? fullName;
  final String? phone;
  final bool isActive;
  final bool? isVerified;
  final String? avatarUrl;
  final String? schoolId;

  String get displayName =>
      (fullName != null && fullName!.trim().isNotEmpty) ? fullName! : username;

  static List<String> _parsePermissions(dynamic raw) {
    if (raw == null) return const [];
    if (raw is List) return raw.map((e) => e.toString()).toList();
    if (raw is String) {
      return raw
          .split(RegExp(r'[\s,]+'))
          .where((p) => p.isNotEmpty)
          .toList();
    }
    return const [];
  }

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id']?.toString() ?? '',
        username: json['username']?.toString() ?? '',
        email: json['email']?.toString() ?? '',
        isSuperAdmin: json['is_super_admin'] == true,
        permissions: _parsePermissions(json['permissions']),
        fullName: json['full_name']?.toString(),
        phone: json['phone']?.toString(),
        isActive: json['is_active'] != false,
        isVerified: json['is_verified'] as bool?,
        avatarUrl:
            (json['avatar_url'] ?? json['profile_photo'])?.toString(),
        schoolId: json['school_id']?.toString(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'username': username,
        'email': email,
        'is_super_admin': isSuperAdmin,
        'permissions': permissions,
        'full_name': fullName,
        'phone': phone,
        'is_active': isActive,
        'is_verified': isVerified,
        'avatar_url': avatarUrl,
        'school_id': schoolId,
      };

  User copyWith({List<String>? permissions, String? avatarUrl}) => User(
        id: id,
        username: username,
        email: email,
        isSuperAdmin: isSuperAdmin,
        permissions: permissions ?? this.permissions,
        fullName: fullName,
        phone: phone,
        isActive: isActive,
        isVerified: isVerified,
        avatarUrl: avatarUrl ?? this.avatarUrl,
        schoolId: schoolId,
      );
}
