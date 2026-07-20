import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/auth_events.dart';
import '../../../core/notifications/push_service.dart';
import '../../../core/providers.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../shared/models/login_response.dart';
import '../data/auth_repository.dart';
import '../domain/app_role.dart';
import 'auth_state.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    ref.watch(dioProvider),
    ref.watch(secureStorageProvider),
  );
});

final authControllerProvider =
    NotifierProvider<AuthController, AuthState>(AuthController.new);

/// Convenience selector for the inferred role.
final roleProvider = Provider<AppRole?>((ref) {
  return ref.watch(authControllerProvider).role;
});

class AuthController extends Notifier<AuthState> {
  late final AuthRepository _repo;
  late final SecureStorage _storage;
  StreamSubscription<void>? _forceLogoutSub;

  @override
  AuthState build() {
    _repo = ref.watch(authRepositoryProvider);
    _storage = ref.watch(secureStorageProvider);

    // Force-logout when the network layer's refresh fails.
    _forceLogoutSub = AuthEvents.instance.onForceLogout.listen((_) {
      _setUnauthenticated();
    });
    ref.onDispose(() => _forceLogoutSub?.cancel());

    // Kick off session restore (async; state starts as `unknown`).
    scheduleMicrotask(bootstrap);
    return const AuthState.unknown();
  }

  /// Restore session on launch: if an access token exists, validate via /auth/me.
  Future<void> bootstrap() async {
    final token = await _storage.accessToken;
    if (token == null || token.isEmpty) {
      _setUnauthenticated();
      return;
    }
    try {
      final user = await _repo.me();
      final slug = await _storage.schoolSlug;
      state = AuthState(
        status: AuthStatus.authenticated,
        user: user,
        role: inferRole(user),
        schoolSlug: slug,
        schoolName: state.schoolName,
      );
      _registerPush();
    } catch (_) {
      await _storage.clearTokens();
      _setUnauthenticated();
    }
  }

  void _registerPush() {
    PushService.instance.registerToken(ref.read(dioProvider)).catchError((_) {});
  }

  Future<void> login({
    required String identifier,
    required String password,
    String? schoolSlug,
  }) async {
    await _run(() => _repo.login(
          identifier: identifier,
          password: password,
          schoolSlug: schoolSlug,
        ));
  }

  Future<void> verifyOtp({
    required String phone,
    required String otp,
    String? schoolSlug,
  }) async {
    await _run(() => _repo.verifyOtp(
          phone: phone,
          otp: otp,
          schoolSlug: schoolSlug,
        ));
  }

  Future<void> sendOtp(String phone, {String? schoolSlug}) async {
    state = state.copyWith(isBusy: true, clearError: true);
    try {
      await _repo.sendOtp(phone, schoolSlug: schoolSlug);
      state = state.copyWith(isBusy: false);
    } on ApiException catch (e) {
      state = state.copyWith(isBusy: false, error: e.message);
      rethrow;
    }
  }

  Future<void> logout() async {
    state = state.copyWith(isBusy: true);
    await PushService.instance.unregister(ref.read(dioProvider));
    await _repo.logout();
    await _storage.setSchoolSlug(null);
    _setUnauthenticated();
  }

  /// Re-fetch the current user (e.g. after profile/permission changes).
  Future<void> refreshUser() async {
    try {
      final user = await _repo.me();
      state = state.copyWith(user: user, role: inferRole(user));
    } catch (_) {/* keep existing state */}
  }

  void clearError() => state = state.copyWith(clearError: true);

  // ── internals ──────────────────────────────────────────────────────────

  Future<void> _run(Future<LoginResponse> Function() action) async {
    state = state.copyWith(isBusy: true, clearError: true);
    try {
      final res = await action();
      state = AuthState(
        status: AuthStatus.authenticated,
        user: res.user,
        role: inferRole(res.user),
        schoolName: res.school?.name,
        schoolSlug: res.school?.slug,
        isBusy: false,
      );
      _registerPush();
    } on ApiException catch (e) {
      state = state.copyWith(isBusy: false, error: e.message);
      rethrow;
    } catch (e) {
      state = state.copyWith(isBusy: false, error: 'Login failed. Please try again.');
      rethrow;
    }
  }

  void _setUnauthenticated() {
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}
