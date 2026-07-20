import 'dart:async';

/// Global bus the network layer uses to tell the app the session is dead
/// (refresh failed) so it can route back to login. Mirrors the Expo app's
/// `authEventEmitter.emit('logout')`.
class AuthEvents {
  AuthEvents._();
  static final AuthEvents instance = AuthEvents._();

  final _controller = StreamController<void>.broadcast();

  Stream<void> get onForceLogout => _controller.stream;

  void emitForceLogout() => _controller.add(null);
}
