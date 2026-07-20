import 'package:flutter_test/flutter_test.dart';
import 'package:sms_flutter/features/auth/domain/app_role.dart';
import 'package:sms_flutter/shared/models/user.dart';

User _user({bool superAdmin = false, List<String> perms = const []}) => User(
      id: '1',
      username: 'u',
      email: 'u@x.com',
      isSuperAdmin: superAdmin,
      permissions: perms,
    );

void main() {
  group('inferRole', () {
    test('super admin flag wins', () {
      expect(inferRole(_user(superAdmin: true)), AppRole.superAdmin);
    });

    test('5+ create/manage perms → admin', () {
      expect(
        inferRole(_user(perms: [
          'students:create',
          'staff:create',
          'fees:manage',
          'classes:create',
          'exams:manage',
        ])),
        AppRole.admin,
      );
    });

    test('attendance:mark → teacher', () {
      expect(inferRole(_user(perms: ['attendance:mark', 'timetable:view'])),
          AppRole.teacher);
    });

    test('fees:view without students:create → parent', () {
      expect(inferRole(_user(perms: ['fees:view', 'announcements:view'])),
          AppRole.parent);
    });

    test('small permission set → student', () {
      expect(inferRole(_user(perms: ['homework:view', 'exams:view'])),
          AppRole.student);
    });
  });

  group('User.permissions parsing', () {
    test('parses space-separated string', () {
      final u = User.fromJson({
        'id': '1',
        'username': 'u',
        'email': 'e',
        'is_super_admin': false,
        'permissions': 'students:view fees:view',
      });
      expect(u.permissions, ['students:view', 'fees:view']);
    });

    test('parses list', () {
      final u = User.fromJson({
        'id': '1',
        'username': 'u',
        'email': 'e',
        'permissions': ['a:b', 'c:d'],
      });
      expect(u.permissions, ['a:b', 'c:d']);
    });

    test('displayName falls back to username', () {
      final u = User.fromJson({'id': '1', 'username': 'jdoe', 'email': 'e'});
      expect(u.displayName, 'jdoe');
    });
  });
}
