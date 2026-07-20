import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../../../shared/utils/format.dart';

class PtmEvent {
  const PtmEvent({required this.id, required this.title, this.date, this.description});
  final String id;
  final String title;
  final DateTime? date;
  final String? description;

  factory PtmEvent.fromJson(Map<String, dynamic> j) => PtmEvent(
        id: j['id']?.toString() ?? '',
        title: (j['title'] ?? 'PTM').toString(),
        date: Fmt.parseDate(j['ptm_date'] ?? j['date']),
        description: j['description']?.toString(),
      );
}

class PtmSlot {
  const PtmSlot({required this.id, this.start, this.end, this.isBooked = false});
  final String id;
  final DateTime? start;
  final DateTime? end;
  final bool isBooked;

  factory PtmSlot.fromJson(Map<String, dynamic> j) => PtmSlot(
        id: j['id']?.toString() ?? '',
        start: Fmt.parseDate(j['slot_start']),
        end: Fmt.parseDate(j['slot_end']),
        isBooked: j['is_booked'] == true,
      );
}

class PtmRepository {
  PtmRepository(this._dio);
  final Dio _dio;

  Future<List<PtmEvent>> events() async {
    try {
      final res = await _dio.get('/ptm/events');
      return Paginated.fromJson(res.data, PtmEvent.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<PtmSlot>> slots(String eventId) async {
    try {
      final res = await _dio.get('/ptm/events/$eventId/slots');
      return Paginated.fromJson(res.data, PtmSlot.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  /// `POST /ptm/bookings` { slot_id, student_id, parent_notes }.
  Future<void> book({
    required String slotId,
    required String studentId,
    String? notes,
  }) async {
    try {
      await _dio.post('/ptm/bookings', data: {
        'slot_id': slotId,
        'student_id': studentId,
        if (notes != null) 'parent_notes': notes,
      });
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
