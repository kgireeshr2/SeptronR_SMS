import 'package:flutter_test/flutter_test.dart';
import 'package:sms_flutter/core/network/dio_client.dart';
import 'package:sms_flutter/shared/models/paginated.dart';

void main() {
  group('unwrapEnvelope', () {
    test('unwraps {success, data}', () {
      final out = DioClient.unwrapEnvelope({
        'success': true,
        'data': {'id': '1'},
        'message': 'ok',
      });
      expect(out, {'id': '1'});
    });

    test('passes through a raw list', () {
      final out = DioClient.unwrapEnvelope([1, 2, 3]);
      expect(out, [1, 2, 3]);
    });

    test('passes through a raw map without envelope', () {
      final out = DioClient.unwrapEnvelope({'id': '1'});
      expect(out, {'id': '1'});
    });
  });

  group('Paginated.fromJson', () {
    Map<String, dynamic> id(Map<String, dynamic> j) => j;

    test('parses raw list', () {
      final p = Paginated.fromJson([
        {'id': '1'},
        {'id': '2'},
      ], id);
      expect(p.items.length, 2);
      expect(p.total, 2);
    });

    test('parses paginated envelope', () {
      final p = Paginated.fromJson({
        'items': [
          {'id': '1'}
        ],
        'total': 10,
        'page': 1,
        'page_size': 1,
        'total_pages': 10,
      }, id);
      expect(p.items.length, 1);
      expect(p.total, 10);
      expect(p.hasMore, isTrue);
    });
  });
}
