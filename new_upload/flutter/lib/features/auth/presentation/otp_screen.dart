import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../application/auth_controller.dart';

class OtpScreen extends ConsumerStatefulWidget {
  const OtpScreen({super.key});

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final _phone = TextEditingController();
  final _otp = TextEditingController();
  final _schoolSlug = TextEditingController();
  bool _sent = false;

  @override
  void dispose() {
    _phone.dispose();
    _otp.dispose();
    _schoolSlug.dispose();
    super.dispose();
  }

  String? get _slug =>
      _schoolSlug.text.trim().isEmpty ? null : _schoolSlug.text.trim();

  Future<void> _send() async {
    if (_phone.text.trim().isEmpty) return;
    try {
      await ref
          .read(authControllerProvider.notifier)
          .sendOtp(_phone.text.trim(), schoolSlug: _slug);
      setState(() => _sent = true);
      _snack('OTP sent', AppColors.success);
    } catch (_) {/* error shown via listener */}
  }

  Future<void> _verify() async {
    if (_otp.text.trim().isEmpty) return;
    try {
      await ref.read(authControllerProvider.notifier).verifyOtp(
            phone: _phone.text.trim(),
            otp: _otp.text.trim(),
            schoolSlug: _slug,
          );
    } catch (_) {/* error shown via listener */}
  }

  void _snack(String msg, Color color) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(msg), backgroundColor: color));
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(authControllerProvider);

    ref.listen(authControllerProvider, (prev, next) {
      if (next.error != null && next.error != prev?.error) {
        _snack(next.error!, AppColors.danger);
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Sign in with OTP')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: _phone,
                keyboardType: TextInputType.phone,
                enabled: !_sent,
                decoration: const InputDecoration(
                  labelText: 'Phone number',
                  prefixIcon: Icon(Icons.phone_outlined),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _schoolSlug,
                enabled: !_sent,
                decoration: const InputDecoration(
                  labelText: 'School code (optional)',
                  prefixIcon: Icon(Icons.business_outlined),
                ),
              ),
              if (_sent) ...[
                const SizedBox(height: 14),
                TextField(
                  controller: _otp,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Enter OTP',
                    prefixIcon: Icon(Icons.password_outlined),
                  ),
                ),
              ],
              const SizedBox(height: 24),
              FilledButton(
                onPressed: state.isBusy ? null : (_sent ? _verify : _send),
                child: state.isBusy
                    ? const SizedBox(
                        height: 22,
                        width: 22,
                        child: CircularProgressIndicator(
                            strokeWidth: 2.4, color: Colors.white),
                      )
                    : Text(_sent ? 'Verify & sign in' : 'Send OTP'),
              ),
              if (_sent)
                TextButton(
                  onPressed: state.isBusy ? null : _send,
                  child: const Text('Resend OTP'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
