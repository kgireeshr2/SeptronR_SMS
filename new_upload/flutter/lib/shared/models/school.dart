class School {
  const School({
    required this.id,
    required this.slug,
    required this.name,
    this.logoUrl,
  });

  final String id;
  final String slug;
  final String name;
  final String? logoUrl;

  factory School.fromJson(Map<String, dynamic> json) => School(
        id: json['id']?.toString() ?? '',
        slug: json['slug']?.toString() ?? '',
        name: json['name']?.toString() ?? '',
        logoUrl: json['logo_url']?.toString(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'slug': slug,
        'name': name,
        'logo_url': logoUrl,
      };
}
