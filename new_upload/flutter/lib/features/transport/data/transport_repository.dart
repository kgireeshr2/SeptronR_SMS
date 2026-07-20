import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../../../shared/models/paginated.dart';
import '../domain/transport_models.dart';

class TransportRepository {
  TransportRepository(this._dio);
  final Dio _dio;

  /// Student/parent: the transport assignment for a student.
  /// `GET /transport/student/{student_id}` → assignment (route/vehicle/stop).
  Future<TransportRoute?> studentTransport(String studentId) async {
    try {
      final res = await _dio.get('/transport/student/$studentId');
      final data = res.data;
      if (data == null || (data is Map && data.isEmpty)) return null;
      if (data is Map) {
        final map = Map<String, dynamic>.from(data);
        // Assignment may nest the route under `route`.
        final route = map['route'] is Map
            ? Map<String, dynamic>.from(map['route'] as Map)
            : map;
        // Surface vehicle/driver if only on the assignment level.
        route.putIfAbsent('vehicle_number',
            () => map['vehicle_number'] ?? map['vehicle']);
        route.putIfAbsent('driver_name', () => map['driver_name']);
        return TransportRoute.fromJson(route);
      }
      return null;
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      throw ApiException.fromDio(e);
    }
  }

  Future<List<TransportRoute>> routes() async {
    try {
      final res = await _dio.get('/transport/routes');
      return Paginated.fromJson(res.data, TransportRoute.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<List<Vehicle>> vehicles() async {
    try {
      final res = await _dio.get('/transport/vehicles');
      return Paginated.fromJson(res.data, Vehicle.fromJson).items;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
