import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/notifications/push_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Initializes Firebase/FCM if native config is present; no-op otherwise.
  await PushService.instance.init();
  runApp(const ProviderScope(child: SmsApp()));
}
