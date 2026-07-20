import 'school.dart';
import 'user.dart';

/// Shape of `response.data` after the `{success,data}` envelope is unwrapped.
class LoginResponse {
  const LoginResponse({
    required this.accessToken,
    required this.user,
    this.school,
  });

  final String accessToken;
  final User user;
  final School? school;

  factory LoginResponse.fromJson(Map<String, dynamic> json) => LoginResponse(
        accessToken: json['access_token']?.toString() ?? '',
        user: User.fromJson(Map<String, dynamic>.from(json['user'] as Map)),
        school: json['school'] is Map
            ? School.fromJson(Map<String, dynamic>.from(json['school'] as Map))
            : null,
      );
}
