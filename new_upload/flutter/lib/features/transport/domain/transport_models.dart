class Vehicle {
  const Vehicle({
    required this.id,
    this.number,
    this.model,
    this.capacity,
    this.driverName,
    this.driverPhone,
  });

  final String id;
  final String? number;
  final String? model;
  final int? capacity;
  final String? driverName;
  final String? driverPhone;

  factory Vehicle.fromJson(Map<String, dynamic> j) => Vehicle(
        id: j['id']?.toString() ?? '',
        number: (j['vehicle_number'] ?? j['registration_number'] ?? j['number'])
            ?.toString(),
        model: (j['model'] ?? j['make'])?.toString(),
        capacity: (j['capacity'] as num?)?.toInt(),
        driverName: j['driver_name']?.toString(),
        driverPhone: j['driver_phone']?.toString(),
      );
}

class RouteStop {
  const RouteStop({required this.name, this.time});
  final String name;
  final String? time;

  factory RouteStop.fromJson(Map<String, dynamic> j) => RouteStop(
        name: (j['name'] ?? j['stop_name'] ?? '').toString(),
        time: (j['time'] ?? j['pickup_time'] ?? j['arrival_time'])?.toString(),
      );
}

class TransportRoute {
  const TransportRoute({
    required this.id,
    required this.name,
    this.vehicleNumber,
    this.driverName,
    this.stops = const [],
  });

  final String id;
  final String name;
  final String? vehicleNumber;
  final String? driverName;
  final List<RouteStop> stops;

  factory TransportRoute.fromJson(Map<String, dynamic> j) => TransportRoute(
        id: j['id']?.toString() ?? '',
        name: (j['name'] ?? j['route_name'] ?? 'Route').toString(),
        vehicleNumber: (j['vehicle_number'] ?? j['vehicle'])?.toString(),
        driverName: j['driver_name']?.toString(),
        stops: (j['stops'] is List)
            ? (j['stops'] as List)
                .whereType<Map>()
                .map((e) => RouteStop.fromJson(Map<String, dynamic>.from(e)))
                .toList()
            : const [],
      );
}
