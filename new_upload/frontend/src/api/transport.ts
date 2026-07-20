import apiClient from './axios';

export type VehicleStatus = 'active' | 'on_route' | 'maintenance' | 'breakdown';
export type RouteType = 'morning' | 'evening' | 'both';
export type SubscriptionType = 'both' | 'pickup' | 'drop';

export interface Vehicle {
  id: string;
  school_id: string;
  registration_number: string;
  vehicle_type: string;
  make?: string;
  model?: string;
  year?: number;
  capacity: number;
  color?: string;
  chassis_number?: string;
  odometer_reading?: number;
  vehicle_status: VehicleStatus;
  // Driver
  driver_id?: string;
  driver_name?: string;
  driver_phone?: string;
  driver_license?: string;
  // Conductor
  conductor_id?: string;
  conductor_name?: string;
  conductor_phone?: string;
  // Documents
  insurance_expiry?: string;
  fitness_expiry?: string;
  permit_expiry?: string;
  // GPS device
  gps_device_id?: string;
  // Live GPS (cached)
  current_latitude?: number;
  current_longitude?: number;
  last_gps_update?: string;
  is_active: boolean;
}

export interface Stop {
  id: string;
  route_id: string;
  name: string;
  address?: string;
  landmark?: string;
  stop_order: number;
  pickup_time?: string;   // morning: when bus arrives to pick up
  drop_time?: string;     // evening: when bus arrives to drop off
  latitude?: number;
  longitude?: number;
  fare: number;
}

export interface Route {
  id: string;
  school_id: string;
  name: string;
  description?: string;
  vehicle_id?: string;
  route_type: RouteType;
  // Starting point (origin / depot)
  starting_point_name?: string;
  start_latitude?: number;
  start_longitude?: number;
  // Ending point (school or last drop)
  ending_point_name?: string;
  end_latitude?: number;
  end_longitude?: number;
  // Morning schedule
  morning_departure_time?: string;   // bus leaves starting point
  school_arrival_time?: string;      // bus reaches school
  // Evening schedule
  evening_departure_time?: string;   // bus leaves school for drops
  // Distance / ETA
  total_distance_km?: number;
  estimated_duration_minutes?: number;
  // Legacy
  start_time?: string;
  end_time?: string;
  is_active: boolean;
  stops: Stop[];
}

export interface StudentTransport {
  id: string;
  student_id: string;
  school_id: string;
  route_id: string;
  stop_id: string;
  academic_year_id: string;
  subscription_type: SubscriptionType;
  is_active: boolean;
}

export interface VehicleMaintenance {
  id: string;
  vehicle_id: string;
  maintenance_type: string;
  description?: string;
  maintenance_date: string;
  next_due_date?: string;
  cost: number;
  vendor_name?: string;
  odometer_reading?: number;
  status: string;
  notes?: string;
}

export interface FuelLog {
  id: string;
  vehicle_id: string;
  fuel_date: string;
  fuel_quantity?: number;
  fuel_cost: number;
  odometer_reading?: number;
  pump_name?: string;
}

export interface GPSLog {
  id: string;
  vehicle_id: string;
  latitude: number;
  longitude: number;
  speed_kmph?: number;
  heading_degrees?: number;
  altitude_meters?: number;
  accuracy_meters?: number;
  recorded_at: string;
  source: string;
  created_at: string;
}

export interface GPSUpdateRequest {
  latitude: number;
  longitude: number;
  speed_kmph?: number;
  heading_degrees?: number;
  altitude_meters?: number;
  accuracy_meters?: number;
  recorded_at?: string;
  source: 'device' | 'driver_app' | 'manual';
}

export interface VehicleLocation {
  vehicle_id: string;
  registration_number: string;
  vehicle_type: string;
  driver_name?: string;
  driver_phone?: string;
  vehicle_status: VehicleStatus;
  current_latitude?: number;
  current_longitude?: number;
  last_gps_update?: string;
  is_active: boolean;
}

export const transportApi = {
  // ── Vehicles ──────────────────────────────────────────────────────────────
  listVehicles: (activeOnly = true) =>
    apiClient.get<Vehicle[]>('/transport/vehicles', { params: { active_only: activeOnly } }),

  getVehicle: (id: string) =>
    apiClient.get<Vehicle>(`/transport/vehicles/${id}`),

  createVehicle: (data: Partial<Vehicle>) =>
    apiClient.post<Vehicle>('/transport/vehicles', data),

  updateVehicle: (id: string, data: Partial<Vehicle>) =>
    apiClient.put<Vehicle>(`/transport/vehicles/${id}`, data),

  deleteVehicle: (id: string) =>
    apiClient.delete(`/transport/vehicles/${id}`),

  getExpiryAlerts: (days = 30) =>
    apiClient.get<object[]>('/transport/vehicles/expiry-alerts', { params: { days } }),

  // ── GPS Tracking ──────────────────────────────────────────────────────────
  recordGPS: (vehicleId: string, data: GPSUpdateRequest) =>
    apiClient.post<GPSLog>(`/transport/vehicles/${vehicleId}/gps`, data),

  getGPSHistory: (vehicleId: string, limit = 100) =>
    apiClient.get<GPSLog[]>(`/transport/vehicles/${vehicleId}/gps`, { params: { limit } }),

  getFleetLocations: () =>
    apiClient.get<VehicleLocation[]>('/transport/fleet/locations'),

  // ── Maintenance ────────────────────────────────────────────────────────────
  listMaintenance: (vehicleId: string) =>
    apiClient.get<VehicleMaintenance[]>(`/transport/vehicles/${vehicleId}/maintenance`),

  addMaintenance: (vehicleId: string, data: Partial<VehicleMaintenance>) =>
    apiClient.post<VehicleMaintenance>(`/transport/vehicles/${vehicleId}/maintenance`, data),

  // ── Fuel Logs ──────────────────────────────────────────────────────────────
  listFuelLogs: (vehicleId: string) =>
    apiClient.get<FuelLog[]>(`/transport/vehicles/${vehicleId}/fuel-logs`),

  addFuelLog: (vehicleId: string, data: Partial<FuelLog>) =>
    apiClient.post<FuelLog>(`/transport/vehicles/${vehicleId}/fuel-logs`, data),

  // ── Routes ─────────────────────────────────────────────────────────────────
  listRoutes: () =>
    apiClient.get<Route[]>('/transport/routes'),

  getRoute: (id: string) =>
    apiClient.get<Route>(`/transport/routes/${id}`),

  createRoute: (data: Partial<Route>) =>
    apiClient.post<Route>('/transport/routes', data),

  updateRoute: (id: string, data: Partial<Route>) =>
    apiClient.put<Route>(`/transport/routes/${id}`, data),

  deleteRoute: (id: string) =>
    apiClient.delete(`/transport/routes/${id}`),

  // ── Stops ──────────────────────────────────────────────────────────────────
  listStops: (routeId: string) =>
    apiClient.get<Stop[]>(`/transport/routes/${routeId}/stops`),

  addStop: (routeId: string, data: Partial<Stop>) =>
    apiClient.post<Stop>(`/transport/routes/${routeId}/stops`, data),

  updateStop: (routeId: string, stopId: string, data: Partial<Stop>) =>
    apiClient.put<Stop>(`/transport/routes/${routeId}/stops/${stopId}`, data),

  deleteStop: (routeId: string, stopId: string) =>
    apiClient.delete(`/transport/routes/${routeId}/stops/${stopId}`),

  // ── Student Assignments ───────────────────────────────────────────────────
  listStudentTransport: (routeId?: string) =>
    apiClient.get<StudentTransport[]>('/transport/students', {
      params: routeId ? { route_id: routeId } : {},
    }),

  assignStudent: (data: Partial<StudentTransport>) =>
    apiClient.post<StudentTransport>('/transport/students', data),

  removeStudentTransport: (id: string) =>
    apiClient.delete(`/transport/students/${id}`),
};
