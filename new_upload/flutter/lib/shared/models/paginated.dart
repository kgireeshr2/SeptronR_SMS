/// Generic paginated wrapper. The backend is inconsistent — some endpoints
/// return `{ items, total, page, page_size, total_pages }`, others a raw list.
/// [Paginated.fromJson] handles both.
class Paginated<T> {
  const Paginated({
    required this.items,
    this.total = 0,
    this.page = 1,
    this.pageSize = 0,
    this.totalPages = 1,
  });

  final List<T> items;
  final int total;
  final int page;
  final int pageSize;
  final int totalPages;

  bool get hasMore => page < totalPages;

  factory Paginated.fromJson(
    dynamic json,
    T Function(Map<String, dynamic>) fromItem,
  ) {
    // Raw list response.
    if (json is List) {
      final items = json
          .whereType<Map>()
          .map((e) => fromItem(Map<String, dynamic>.from(e)))
          .toList();
      return Paginated<T>(
        items: items,
        total: items.length,
        pageSize: items.length,
      );
    }

    if (json is Map) {
      final rawItems = (json['items'] ?? json['data'] ?? json['results']);
      final items = (rawItems is List)
          ? rawItems
              .whereType<Map>()
              .map((e) => fromItem(Map<String, dynamic>.from(e)))
              .toList()
          : <T>[];
      return Paginated<T>(
        items: items,
        total: (json['total'] as num?)?.toInt() ?? items.length,
        page: (json['page'] as num?)?.toInt() ?? 1,
        pageSize: (json['page_size'] as num?)?.toInt() ?? items.length,
        totalPages: (json['total_pages'] as num?)?.toInt() ?? 1,
      );
    }

    return Paginated<T>(items: const []);
  }
}
