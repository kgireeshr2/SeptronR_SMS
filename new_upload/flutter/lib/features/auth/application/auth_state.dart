import '../../../shared/models/user.dart';
import '../domain/app_role.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

/// Immutable session snapshot held by [AuthController].
class AuthState {
  const AuthState({
    required this.status,
    this.user,
    this.role,
    this.schoolName,
    this.schoolSlug,
    this.isBusy = false,
    this.error,
  });

  final AuthStatus status;
  final User? user;
  final AppRole? role;
  final String? schoolName;
  final String? schoolSlug;
  final bool isBusy;
  final String? error;

  const AuthState.unknown() : this(status: AuthStatus.unknown);

  bool get isAuthenticated => status == AuthStatus.authenticated;

  List<String> get permissions => user?.permissions ?? const [];

  /// Mirrors authStore.hasPermission: super admin → all; else exact match.
  bool can(String module, String action) {
    if (user == null) return false;
    if (user!.isSuperAdmin) return true;
    return permissions.contains('$module:$action');
  }

  bool hasRole(List<AppRole> roles) => role != null && roles.contains(role);

  AuthState copyWith({
    AuthStatus? status,
    User? user,
    AppRole? role,
    String? schoolName,
    String? schoolSlug,
    bool? isBusy,
    String? error,
    bool clearError = false,
    bool clearUser = false,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: clearUser ? null : (user ?? this.user),
      role: clearUser ? null : (role ?? this.role),
      schoolName: schoolName ?? this.schoolName,
      schoolSlug: schoolSlug ?? this.schoolSlug,
      isBusy: isBusy ?? this.isBusy,
      error: clearError ? null : (error ?? this.error),
    );
  }
}
