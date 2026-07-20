class Announcement {
  const Announcement({
    required this.id,
    required this.title,
    this.content,
    this.targetRoles = const [],
    this.publishedAt,
    this.createdByName,
    this.isRead = false,
  });

  final String id;
  final String title;
  final String? content;
  final List<String> targetRoles;
  final DateTime? publishedAt;
  final String? createdByName;
  final bool isRead;

  factory Announcement.fromJson(Map<String, dynamic> j) => Announcement(
        id: j['id']?.toString() ?? '',
        title: j['title']?.toString() ?? '',
        content: (j['content'] ?? j['body'] ?? j['message'])?.toString(),
        targetRoles: (j['target_roles'] is List)
            ? (j['target_roles'] as List).map((e) => e.toString()).toList()
            : const [],
        publishedAt: _date(j['published_at'] ?? j['created_at']),
        createdByName: (j['created_by_name'] ?? j['author_name'])?.toString(),
        isRead: j['is_read'] == true,
      );
}

class AppNotification {
  const AppNotification({
    required this.id,
    required this.title,
    this.message,
    this.type,
    this.isRead = false,
    this.createdAt,
  });

  final String id;
  final String title;
  final String? message;
  final String? type;
  final bool isRead;
  final DateTime? createdAt;

  factory AppNotification.fromJson(Map<String, dynamic> j) => AppNotification(
        id: j['id']?.toString() ?? '',
        title: j['title']?.toString() ?? '',
        message: (j['message'] ?? j['body'])?.toString(),
        type: j['type']?.toString(),
        isRead: j['is_read'] == true,
        createdAt: _date(j['created_at']),
      );
}

DateTime? _date(dynamic v) {
  if (v == null) return null;
  return DateTime.tryParse(v.toString())?.toLocal();
}
