import React, { useEffect, useState, useCallback } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import {
  transportApi,
  Vehicle, Route, Stop, StudentTransport, VehicleMaintenance, FuelLog,
  GPSLog, VehicleLocation, VehicleStatus, RouteType,
} from '@/api/transport';
import { formatDateTime } from '@utils/formatters';

type Tab = 'vehicles' | 'routes' | 'gps' | 'students' | 'maintenance' | 'fuel';

const VEHICLE_TYPES = ['bus', 'van', 'auto', 'car', 'minibus', 'other'];
const ROUTE_TYPES: { value: RouteType; label: string }[] = [
  { value: 'both',    label: '↕ Both (Morning & Evening)' },
  { value: 'morning', label: '↑ Morning Only (Home → School)' },
  { value: 'evening', label: '↓ Evening Only (School → Home)' },
];
const VEHICLE_STATUSES: { value: VehicleStatus; label: string; color: string }[] = [
  { value: 'active',      label: 'Active',       color: 'bg-green-100 text-green-700' },
  { value: 'on_route',    label: 'On Route',     color: 'bg-blue-100 text-blue-700' },
  { value: 'maintenance', label: 'Maintenance',  color: 'bg-amber-100 text-amber-700' },
  { value: 'breakdown',   label: 'Breakdown',    color: 'bg-red-100 text-red-700' },
];

function statusBadge(status: VehicleStatus) {
  const s = VEHICLE_STATUSES.find(x => x.value === status);
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${s?.color ?? 'bg-gray-100 text-gray-600'}`}>
      {s?.label ?? status}
    </span>
  );
}

function hasGPS(v: Vehicle | VehicleLocation) {
  return v.current_latitude != null && v.current_longitude != null;
}

function mapsLink(lat: number, lng: number) {
  return `https://www.google.com/maps?q=${lat},${lng}`;
}

// ─── Shared form helpers (must be outside component to avoid remount on rerender) ──
const inp = 'border rounded px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-300';

const F = ({ label, children, span = 1 }: { label: string; children: React.ReactNode; span?: number }) => (
  <div className={span === 2 ? 'col-span-2' : ''}>
    <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
    {children}
  </div>
);

// ─── Main Component ──────────────────────────────────────────────────────────

const TransportPage: React.FC = () => {
  const [tab, setTab] = useState<Tab>('vehicles');
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [routes, setRoutes]     = useState<Route[]>([]);
  const [students, setStudents] = useState<StudentTransport[]>([]);
  const [fleet, setFleet]       = useState<VehicleLocation[]>([]);
  const [loading, setLoading]   = useState(false);
  const [alerts, setAlerts]     = useState<any[]>([]);

  // Selected vehicle for maintenance / fuel / GPS detail
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [maintenance, setMaintenance]         = useState<VehicleMaintenance[]>([]);
  const [fuelLogs, setFuelLogs]               = useState<FuelLog[]>([]);
  const [gpsHistory, setGpsHistory]           = useState<GPSLog[]>([]);

  // ── Vehicle form ──────────────────────────────────────────────────────────
  const EMPTY_VEHICLE = {
    registration_number: '', vehicle_type: 'bus', capacity: 40, year: '',
    make: '', model: '', color: '', chassis_number: '',
    vehicle_status: 'active' as VehicleStatus,
    insurance_expiry: '', fitness_expiry: '', permit_expiry: '',
    gps_device_id: '',
    driver_name: '', driver_phone: '', driver_license: '',
    conductor_name: '', conductor_phone: '',
  };
  const [showVehicleForm, setShowVehicleForm]   = useState(false);
  const [editingVehicle, setEditingVehicle]     = useState<Vehicle | null>(null);
  const [vehicleForm, setVehicleForm]           = useState(EMPTY_VEHICLE);
  const [vehicleSaving, setVehicleSaving]       = useState(false);

  // ── Route form ────────────────────────────────────────────────────────────
  const EMPTY_ROUTE = {
    name: '', description: '', route_type: 'both' as RouteType,
    vehicle_id: '',
    starting_point_name: '', start_latitude: '', start_longitude: '',
    ending_point_name: '',   end_latitude: '',   end_longitude: '',
    morning_departure_time: '', school_arrival_time: '', evening_departure_time: '',
    total_distance_km: '', estimated_duration_minutes: '',
  };
  const [showRouteForm, setShowRouteForm]   = useState(false);
  const [editingRoute, setEditingRoute]     = useState<Route | null>(null);
  const [routeForm, setRouteForm]           = useState(EMPTY_ROUTE);
  const [routeSaving, setRouteSaving]       = useState(false);

  // ── Stop form ─────────────────────────────────────────────────────────────
  const EMPTY_STOP = {
    name: '', address: '', landmark: '', stop_order: 1,
    pickup_time: '', drop_time: '',
    latitude: '', longitude: '', fare: 0,
  };
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
  const [showStopForm, setShowStopForm]   = useState(false);
  const [stopForm, setStopForm]           = useState(EMPTY_STOP);
  const [stopSaving, setStopSaving]       = useState(false);
  const [stopsView, setStopsView]         = useState<'morning' | 'evening'>('morning');

  // ── Maintenance form ──────────────────────────────────────────────────────
  const EMPTY_MAINT = {
    maintenance_type: '', description: '', maintenance_date: '',
    next_due_date: '', cost: 0, vendor_name: '', odometer_reading: '', notes: '', status: 'completed',
  };
  const [showMaintForm, setShowMaintForm] = useState(false);
  const [maintForm, setMaintForm]         = useState(EMPTY_MAINT);

  // ── Fuel form ─────────────────────────────────────────────────────────────
  const EMPTY_FUEL = { fuel_date: '', fuel_quantity: '', fuel_cost: 0, odometer_reading: '', pump_name: '' };
  const [showFuelForm, setShowFuelForm] = useState(false);
  const [fuelForm, setFuelForm]         = useState(EMPTY_FUEL);

  // ── GPS manual ping form ───────────────────────────────────────────────────
  const [showGPSForm, setShowGPSForm] = useState(false);
  const [gpsVehicleId, setGpsVehicleId] = useState('');
  const [gpsForm, setGpsForm] = useState({ latitude: '', longitude: '', speed_kmph: '', heading_degrees: '' });

  // ─── Loaders ───────────────────────────────────────────────────────────────

  const loadVehicles = useCallback(async () => {
    setLoading(true);
    try {
      const r: any = await transportApi.listVehicles(false); // false = all, not just active
      setVehicles(Array.isArray(r) ? r : (r?.data ?? []));
      const a: any = await transportApi.getExpiryAlerts(30);
      setAlerts(Array.isArray(a) ? a : (a?.data ?? []));
    } finally { setLoading(false); }
  }, []);

  const loadRoutes = useCallback(async () => {
    setLoading(true);
    try {
      const r: any = await transportApi.listRoutes();
      const list: Route[] = Array.isArray(r) ? r : (r?.data ?? []);
      setRoutes(list);
      // Keep selectedRoute in sync with fresh data from server
      setSelectedRoute(prev => prev ? (list.find(rt => rt.id === prev.id) ?? prev) : null);
    } finally { setLoading(false); }
  }, []);

  const loadFleet = useCallback(async () => {
    setLoading(true);
    try {
      const r: any = await transportApi.getFleetLocations();
      setFleet(Array.isArray(r) ? r : (r?.data ?? []));
    } finally { setLoading(false); }
  }, []);

  const loadStudents = useCallback(async () => {
    setLoading(true);
    try {
      const r: any = await transportApi.listStudentTransport();
      setStudents(Array.isArray(r) ? r : (r?.data ?? []));
    } finally { setLoading(false); }
  }, []);

  const loadMaintenance = useCallback(async (vehicleId: string) => {
    const r: any = await transportApi.listMaintenance(vehicleId);
    setMaintenance(Array.isArray(r) ? r : (r?.data ?? []));
  }, []);

  const loadFuelLogs = useCallback(async (vehicleId: string) => {
    const r: any = await transportApi.listFuelLogs(vehicleId);
    setFuelLogs(Array.isArray(r) ? r : (r?.data ?? []));
  }, []);

  const loadGPSHistory = useCallback(async (vehicleId: string) => {
    const r: any = await transportApi.getGPSHistory(vehicleId, 50);
    setGpsHistory(Array.isArray(r) ? r : (r?.data ?? []));
  }, []);

  useEffect(() => {
    if (tab === 'vehicles')    loadVehicles();
    else if (tab === 'routes') loadRoutes();
    else if (tab === 'gps')    loadFleet();
    else if (tab === 'students') loadStudents();
    else if (tab === 'maintenance' && selectedVehicle) loadMaintenance(selectedVehicle.id);
    else if (tab === 'fuel' && selectedVehicle) loadFuelLogs(selectedVehicle.id);
  }, [tab, selectedVehicle]);

  // ─── Vehicle CRUD ──────────────────────────────────────────────────────────

  const openVehicleForm = (v?: Vehicle) => {
    if (v) {
      setEditingVehicle(v);
      setVehicleForm({
        registration_number: v.registration_number,
        vehicle_type: v.vehicle_type,
        capacity: v.capacity,
        year: v.year?.toString() ?? '',
        make: v.make ?? '',
        model: v.model ?? '',
        color: v.color ?? '',
        chassis_number: v.chassis_number ?? '',
        vehicle_status: v.vehicle_status,
        insurance_expiry: v.insurance_expiry ?? '',
        fitness_expiry: v.fitness_expiry ?? '',
        permit_expiry: v.permit_expiry ?? '',
        gps_device_id: v.gps_device_id ?? '',
        driver_name: v.driver_name ?? '',
        driver_phone: v.driver_phone ?? '',
        driver_license: v.driver_license ?? '',
        conductor_name: v.conductor_name ?? '',
        conductor_phone: v.conductor_phone ?? '',
      });
    } else {
      setEditingVehicle(null);
      setVehicleForm(EMPTY_VEHICLE);
    }
    setShowVehicleForm(true);
  };

  const handleSaveVehicle = async () => {
    if (!vehicleForm.registration_number) return;
    setVehicleSaving(true);
    try {
      const payload: any = {
        ...vehicleForm,
        capacity: Number(vehicleForm.capacity),
        year: vehicleForm.year ? Number(vehicleForm.year) : null,
        insurance_expiry: vehicleForm.insurance_expiry || null,
        fitness_expiry: vehicleForm.fitness_expiry || null,
        permit_expiry: vehicleForm.permit_expiry || null,
        gps_device_id: vehicleForm.gps_device_id || null,
        color: vehicleForm.color || null,
        chassis_number: vehicleForm.chassis_number || null,
      };
      if (editingVehicle) {
        await transportApi.updateVehicle(editingVehicle.id, payload);
      } else {
        await transportApi.createVehicle(payload);
      }
      setShowVehicleForm(false);
      loadVehicles();
    } finally { setVehicleSaving(false); }
  };

  const handleDeleteVehicle = async (id: string) => {
    if (!confirm('Delete this vehicle? This will also remove all GPS logs.')) return;
    await transportApi.deleteVehicle(id);
    loadVehicles();
  };

  // ─── Route CRUD ────────────────────────────────────────────────────────────

  const openRouteForm = (r?: Route) => {
    if (r) {
      setEditingRoute(r);
      setRouteForm({
        name: r.name, description: r.description ?? '',
        route_type: r.route_type ?? 'both',
        vehicle_id: r.vehicle_id ?? '',
        starting_point_name: r.starting_point_name ?? '',
        start_latitude: r.start_latitude?.toString() ?? '',
        start_longitude: r.start_longitude?.toString() ?? '',
        ending_point_name: r.ending_point_name ?? '',
        end_latitude: r.end_latitude?.toString() ?? '',
        end_longitude: r.end_longitude?.toString() ?? '',
        morning_departure_time: r.morning_departure_time ?? '',
        school_arrival_time: r.school_arrival_time ?? '',
        evening_departure_time: r.evening_departure_time ?? '',
        total_distance_km: r.total_distance_km?.toString() ?? '',
        estimated_duration_minutes: r.estimated_duration_minutes?.toString() ?? '',
      });
    } else {
      setEditingRoute(null);
      setRouteForm(EMPTY_ROUTE);
    }
    setShowRouteForm(true);
  };

  const handleSaveRoute = async () => {
    if (!routeForm.name) return;
    setRouteSaving(true);
    try {
      const payload: any = {
        ...routeForm,
        vehicle_id: routeForm.vehicle_id || null,
        start_latitude: routeForm.start_latitude ? Number(routeForm.start_latitude) : null,
        start_longitude: routeForm.start_longitude ? Number(routeForm.start_longitude) : null,
        end_latitude: routeForm.end_latitude ? Number(routeForm.end_latitude) : null,
        end_longitude: routeForm.end_longitude ? Number(routeForm.end_longitude) : null,
        total_distance_km: routeForm.total_distance_km ? Number(routeForm.total_distance_km) : null,
        estimated_duration_minutes: routeForm.estimated_duration_minutes ? Number(routeForm.estimated_duration_minutes) : null,
        morning_departure_time: routeForm.morning_departure_time || null,
        school_arrival_time: routeForm.school_arrival_time || null,
        evening_departure_time: routeForm.evening_departure_time || null,
        starting_point_name: routeForm.starting_point_name || null,
        ending_point_name: routeForm.ending_point_name || null,
      };
      if (editingRoute) {
        await transportApi.updateRoute(editingRoute.id, payload);
      } else {
        await transportApi.createRoute(payload);
      }
      setShowRouteForm(false);
      loadRoutes();
    } finally { setRouteSaving(false); }
  };

  const handleDeleteRoute = async (id: string) => {
    if (!confirm('Delete this route and all its stops?')) return;
    await transportApi.deleteRoute(id);
    loadRoutes();
    if (selectedRoute?.id === id) setSelectedRoute(null);
  };

  // ─── Stop CRUD ─────────────────────────────────────────────────────────────

  const handleAddStop = async () => {
    if (!selectedRoute || !stopForm.name) return;
    setStopSaving(true);
    try {
      await transportApi.addStop(selectedRoute.id, {
        ...stopForm,
        stop_order: Number(stopForm.stop_order),
        fare: Number(stopForm.fare),
        latitude: stopForm.latitude ? Number(stopForm.latitude) : null,
        longitude: stopForm.longitude ? Number(stopForm.longitude) : null,
        pickup_time: stopForm.pickup_time || undefined,
        drop_time: stopForm.drop_time || undefined,
        address: stopForm.address || undefined,
        landmark: stopForm.landmark || undefined,
      } as any);
      setShowStopForm(false);
      setStopForm(EMPTY_STOP);
      // Refresh route to get updated stops
      const r: any = await transportApi.getRoute(selectedRoute.id);
      const updated = r?.data ?? r;
      setSelectedRoute(updated);
      setRoutes(prev => prev.map(rt => rt.id === updated.id ? updated : rt));
    } finally { setStopSaving(false); }
  };

  const handleDeleteStop = async (routeId: string, stopId: string) => {
    if (!confirm('Remove this stop?')) return;
    await transportApi.deleteStop(routeId, stopId);
    const r: any = await transportApi.getRoute(routeId);
    const updated = r?.data ?? r;
    setSelectedRoute(updated);
    setRoutes(prev => prev.map(rt => rt.id === updated.id ? updated : rt));
  };

  // ─── Maintenance ───────────────────────────────────────────────────────────

  const handleAddMaintenance = async () => {
    if (!selectedVehicle || !maintForm.maintenance_type || !maintForm.maintenance_date) return;
    await transportApi.addMaintenance(selectedVehicle.id, {
      vehicle_id: selectedVehicle.id,
      ...maintForm,
      cost: Number(maintForm.cost),
      odometer_reading: maintForm.odometer_reading ? Number(maintForm.odometer_reading) : undefined,
      next_due_date: maintForm.next_due_date || undefined,
    } as any);
    setShowMaintForm(false);
    setMaintForm(EMPTY_MAINT);
    loadMaintenance(selectedVehicle.id);
  };

  // ─── Fuel Logs ─────────────────────────────────────────────────────────────

  const handleAddFuelLog = async () => {
    if (!selectedVehicle || !fuelForm.fuel_date) return;
    await transportApi.addFuelLog(selectedVehicle.id, {
      vehicle_id: selectedVehicle.id,
      ...fuelForm,
      fuel_cost: Number(fuelForm.fuel_cost),
      fuel_quantity: fuelForm.fuel_quantity ? Number(fuelForm.fuel_quantity) : undefined,
      odometer_reading: fuelForm.odometer_reading ? Number(fuelForm.odometer_reading) : undefined,
    } as any);
    setShowFuelForm(false);
    setFuelForm(EMPTY_FUEL);
    loadFuelLogs(selectedVehicle.id);
  };

  // ─── GPS Manual Ping ───────────────────────────────────────────────────────

  const handleManualGPS = async () => {
    if (!gpsVehicleId || !gpsForm.latitude || !gpsForm.longitude) return;
    await transportApi.recordGPS(gpsVehicleId, {
      latitude: Number(gpsForm.latitude),
      longitude: Number(gpsForm.longitude),
      speed_kmph: gpsForm.speed_kmph ? Number(gpsForm.speed_kmph) : undefined,
      heading_degrees: gpsForm.heading_degrees ? Number(gpsForm.heading_degrees) : undefined,
      source: 'manual',
    });
    setShowGPSForm(false);
    setGpsForm({ latitude: '', longitude: '', speed_kmph: '', heading_degrees: '' });
    loadFleet();
    if (gpsVehicleId) loadGPSHistory(gpsVehicleId);
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'vehicles',    label: 'Vehicles',       icon: '🚌' },
    { id: 'routes',      label: 'Routes & Stops',  icon: '🗺️' },
    { id: 'gps',         label: 'GPS Tracking',    icon: '📍' },
    { id: 'students',    label: 'Assignments',     icon: '👨‍🎓' },
    { id: 'maintenance', label: 'Maintenance',     icon: '🔧' },
    { id: 'fuel',        label: 'Fuel Logs',       icon: '⛽' },
  ];



  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <div>
      <PageHeader title="Transport Management" />

      {/* Expiry Alerts */}
      {alerts.length > 0 && (
        <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 p-3">
          <p className="text-sm font-semibold text-amber-800 mb-1">⚠️ Document Expiry Alerts ({alerts.length})</p>
          <div className="flex flex-wrap gap-2">
            {alerts.slice(0, 6).map((a, i) => (
              <span key={i} className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-700">
                {a.registration_number} — {a.document} expires in {a.days_remaining}d
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition flex items-center gap-1.5 ${
              tab === t.id
                ? 'bg-blue-600 text-white shadow'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* ═══════════════ VEHICLES TAB ═══════════════ */}
      {tab === 'vehicles' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button onClick={() => openVehicleForm()} className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
              + Add Vehicle
            </button>
          </div>

          {showVehicleForm && (
            <div className="mb-6 rounded-xl border bg-white p-5 shadow-sm">
              <h3 className="font-semibold mb-4 text-gray-800">{editingVehicle ? 'Edit Vehicle' : 'Add Vehicle'}</h3>

              <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Basic Information</p>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <F label="Registration No. *">
                  <input className={inp} placeholder="e.g. TN01AB1234" value={vehicleForm.registration_number}
                    onChange={e => setVehicleForm({ ...vehicleForm, registration_number: e.target.value })} />
                </F>
                <F label="Vehicle Type">
                  <select className={inp} value={vehicleForm.vehicle_type}
                    onChange={e => setVehicleForm({ ...vehicleForm, vehicle_type: e.target.value })}>
                    {VEHICLE_TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                  </select>
                </F>
                <F label="Status">
                  <select className={inp} value={vehicleForm.vehicle_status}
                    onChange={e => setVehicleForm({ ...vehicleForm, vehicle_status: e.target.value as VehicleStatus })}>
                    {VEHICLE_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                </F>
                <F label="Make"><input className={inp} placeholder="e.g. Tata" value={vehicleForm.make} onChange={e => setVehicleForm({ ...vehicleForm, make: e.target.value })} /></F>
                <F label="Model"><input className={inp} placeholder="e.g. Starbus" value={vehicleForm.model} onChange={e => setVehicleForm({ ...vehicleForm, model: e.target.value })} /></F>
                <F label="Year"><input type="number" className={inp} placeholder="2022" value={vehicleForm.year} onChange={e => setVehicleForm({ ...vehicleForm, year: e.target.value })} /></F>
                <F label="Capacity"><input type="number" className={inp} value={vehicleForm.capacity} onChange={e => setVehicleForm({ ...vehicleForm, capacity: parseInt(e.target.value) || 40 })} /></F>
                <F label="Color"><input className={inp} placeholder="e.g. Yellow" value={vehicleForm.color} onChange={e => setVehicleForm({ ...vehicleForm, color: e.target.value })} /></F>
                <F label="Chassis No."><input className={inp} placeholder="Chassis number" value={vehicleForm.chassis_number} onChange={e => setVehicleForm({ ...vehicleForm, chassis_number: e.target.value })} /></F>
              </div>

              <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Documents & Compliance</p>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <F label="Insurance Expiry"><input type="date" className={inp} value={vehicleForm.insurance_expiry} onChange={e => setVehicleForm({ ...vehicleForm, insurance_expiry: e.target.value })} /></F>
                <F label="Fitness Expiry"><input type="date" className={inp} value={vehicleForm.fitness_expiry} onChange={e => setVehicleForm({ ...vehicleForm, fitness_expiry: e.target.value })} /></F>
                <F label="Permit Expiry"><input type="date" className={inp} value={vehicleForm.permit_expiry} onChange={e => setVehicleForm({ ...vehicleForm, permit_expiry: e.target.value })} /></F>
                <F label="GPS Device ID"><input className={inp} placeholder="Device serial / IMEI" value={vehicleForm.gps_device_id} onChange={e => setVehicleForm({ ...vehicleForm, gps_device_id: e.target.value })} /></F>
              </div>

              <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Driver Details</p>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <F label="Driver Name"><input className={inp} placeholder="Driver name" value={vehicleForm.driver_name} onChange={e => setVehicleForm({ ...vehicleForm, driver_name: e.target.value })} /></F>
                <F label="Driver Phone"><input className={inp} placeholder="+91 XXXXX XXXXX" value={vehicleForm.driver_phone} onChange={e => setVehicleForm({ ...vehicleForm, driver_phone: e.target.value })} /></F>
                <F label="License No."><input className={inp} placeholder="DL number" value={vehicleForm.driver_license} onChange={e => setVehicleForm({ ...vehicleForm, driver_license: e.target.value })} /></F>
              </div>

              <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Conductor Details</p>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <F label="Conductor Name"><input className={inp} placeholder="Conductor name" value={vehicleForm.conductor_name} onChange={e => setVehicleForm({ ...vehicleForm, conductor_name: e.target.value })} /></F>
                <F label="Conductor Phone"><input className={inp} placeholder="+91 XXXXX XXXXX" value={vehicleForm.conductor_phone} onChange={e => setVehicleForm({ ...vehicleForm, conductor_phone: e.target.value })} /></F>
              </div>

              <div className="flex gap-2 pt-2 border-t">
                <button onClick={handleSaveVehicle} disabled={vehicleSaving}
                  className="rounded bg-blue-600 px-5 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-60">
                  {vehicleSaving ? 'Saving…' : 'Save Vehicle'}
                </button>
                <button onClick={() => setShowVehicleForm(false)} className="rounded border px-4 py-1.5 text-sm hover:bg-gray-50">Cancel</button>
              </div>
            </div>
          )}

          {loading ? <p className="text-center text-gray-400 py-10">Loading…</p> : (
            <div className="overflow-x-auto rounded-xl border bg-white shadow-sm">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                  <tr>
                    {['Reg. No.', 'Type/Color', 'Make/Model', 'Cap.', 'Status', 'Driver', 'Conductor', 'GPS', 'Docs Expiry', ''].map(h => (
                      <th key={h} className="px-3 py-3 text-left whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {vehicles.length === 0 ? (
                    <tr><td colSpan={10} className="text-center py-10 text-gray-400">No vehicles added yet</td></tr>
                  ) : vehicles.map(v => (
                    <tr key={v.id} className="hover:bg-gray-50">
                      <td className="px-3 py-3 font-mono font-semibold text-sm">{v.registration_number}</td>
                      <td className="px-3 py-3">
                        <div className="capitalize font-medium">{v.vehicle_type}</div>
                        {v.color && <div className="text-xs text-gray-400">{v.color}</div>}
                      </td>
                      <td className="px-3 py-3">{[v.make, v.model].filter(Boolean).join(' ') || '—'}</td>
                      <td className="px-3 py-3 text-center">{v.capacity}</td>
                      <td className="px-3 py-3">{statusBadge(v.vehicle_status)}</td>
                      <td className="px-3 py-3">
                        {v.driver_name ? <>
                          <div className="font-medium">{v.driver_name}</div>
                          {v.driver_phone && <div className="text-xs text-gray-400">{v.driver_phone}</div>}
                          {v.driver_license && <div className="text-xs text-gray-400">Lic: {v.driver_license}</div>}
                        </> : '—'}
                      </td>
                      <td className="px-3 py-3">
                        {v.conductor_name ? <>
                          <div className="font-medium">{v.conductor_name}</div>
                          {v.conductor_phone && <div className="text-xs text-gray-400">{v.conductor_phone}</div>}
                        </> : '—'}
                      </td>
                      <td className="px-3 py-3">
                        {hasGPS(v) ? (
                          <a href={mapsLink(v.current_latitude!, v.current_longitude!)} target="_blank" rel="noreferrer"
                            className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                            📍 View
                          </a>
                        ) : v.gps_device_id ? (
                          <span className="text-xs text-amber-600">Device: {v.gps_device_id.slice(0, 8)}</span>
                        ) : <span className="text-xs text-gray-400">—</span>}
                      </td>
                      <td className="px-3 py-3 text-xs">
                        {v.insurance_expiry && <div>Ins: {v.insurance_expiry}</div>}
                        {v.fitness_expiry && <div>Fit: {v.fitness_expiry}</div>}
                        {v.permit_expiry && <div>Pmt: {v.permit_expiry}</div>}
                        {!v.insurance_expiry && !v.fitness_expiry && !v.permit_expiry && '—'}
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-2">
                          <button onClick={() => openVehicleForm(v)} className="text-xs text-blue-600 hover:underline">Edit</button>
                          <button onClick={() => { setSelectedVehicle(v); setTab('maintenance'); }} className="text-xs text-gray-500 hover:underline">Maint.</button>
                          <button onClick={() => handleDeleteVehicle(v.id)} className="text-xs text-red-500 hover:underline">Del</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════ ROUTES & STOPS TAB ═══════════════ */}
      {tab === 'routes' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
          {/* Route list */}
          <div className="lg:col-span-2">
            <div className="mb-3 flex justify-between items-center">
              <h3 className="font-semibold text-gray-700">Routes</h3>
              <button onClick={() => openRouteForm()} className="rounded bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700">+ Route</button>
            </div>

            {showRouteForm && (
              <div className="mb-4 rounded-xl border bg-white p-4 shadow-sm">
                <h4 className="font-semibold mb-3 text-sm">{editingRoute ? 'Edit Route' : 'Add Route'}</h4>
                <div className="grid grid-cols-2 gap-2">
                  <F label="Route Name *"><input className={inp} placeholder="Route A - North Zone" value={routeForm.name} onChange={e => setRouteForm({ ...routeForm, name: e.target.value })} /></F>
                  <F label="Type">
                    <select className={inp} value={routeForm.route_type} onChange={e => setRouteForm({ ...routeForm, route_type: e.target.value as RouteType })}>
                      {ROUTE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </F>
                  <F label="Assigned Vehicle">
                    <select className={inp} value={routeForm.vehicle_id} onChange={e => setRouteForm({ ...routeForm, vehicle_id: e.target.value })}>
                      <option value="">— Not assigned —</option>
                      {vehicles.map(v => <option key={v.id} value={v.id}>{v.registration_number} ({v.vehicle_type})</option>)}
                    </select>
                  </F>
                  <F label="Description"><input className={inp} placeholder="Optional description" value={routeForm.description} onChange={e => setRouteForm({ ...routeForm, description: e.target.value })} /></F>

                  <div className="col-span-2 border-t pt-2 mt-1">
                    <p className="text-xs font-semibold text-blue-600 mb-2">📍 Starting Point (Origin / Depot)</p>
                    <div className="grid grid-cols-3 gap-2">
                      <F label="Location Name" span={2}><input className={inp} placeholder="e.g. Bus Depot, North Colony Entry" value={routeForm.starting_point_name} onChange={e => setRouteForm({ ...routeForm, starting_point_name: e.target.value })} /></F>
                      <div />
                      <F label="Latitude"><input type="number" step="0.0000001" className={inp} placeholder="12.9716" value={routeForm.start_latitude} onChange={e => setRouteForm({ ...routeForm, start_latitude: e.target.value })} /></F>
                      <F label="Longitude"><input type="number" step="0.0000001" className={inp} placeholder="77.5946" value={routeForm.start_longitude} onChange={e => setRouteForm({ ...routeForm, start_longitude: e.target.value })} /></F>
                    </div>
                  </div>

                  <div className="col-span-2 border-t pt-2 mt-1">
                    <p className="text-xs font-semibold text-green-600 mb-2">🏫 Ending Point (School / Last Destination)</p>
                    <div className="grid grid-cols-3 gap-2">
                      <F label="Location Name" span={2}><input className={inp} placeholder="e.g. School Main Gate" value={routeForm.ending_point_name} onChange={e => setRouteForm({ ...routeForm, ending_point_name: e.target.value })} /></F>
                      <div />
                      <F label="Latitude"><input type="number" step="0.0000001" className={inp} placeholder="12.9716" value={routeForm.end_latitude} onChange={e => setRouteForm({ ...routeForm, end_latitude: e.target.value })} /></F>
                      <F label="Longitude"><input type="number" step="0.0000001" className={inp} placeholder="77.5946" value={routeForm.end_longitude} onChange={e => setRouteForm({ ...routeForm, end_longitude: e.target.value })} /></F>
                    </div>
                  </div>

                  <div className="col-span-2 border-t pt-2 mt-1">
                    <p className="text-xs font-semibold text-amber-600 mb-2">🌅 Morning Schedule (Home → School)</p>
                    <div className="grid grid-cols-2 gap-2">
                      <F label="Bus Departs Starting Point"><input type="time" className={inp} value={routeForm.morning_departure_time} onChange={e => setRouteForm({ ...routeForm, morning_departure_time: e.target.value })} /></F>
                      <F label="Bus Arrives at School"><input type="time" className={inp} value={routeForm.school_arrival_time} onChange={e => setRouteForm({ ...routeForm, school_arrival_time: e.target.value })} /></F>
                    </div>
                  </div>

                  <div className="col-span-2 border-t pt-2 mt-1">
                    <p className="text-xs font-semibold text-indigo-600 mb-2">🌆 Evening Schedule (School → Home)</p>
                    <div className="grid grid-cols-2 gap-2">
                      <F label="Bus Departs School"><input type="time" className={inp} value={routeForm.evening_departure_time} onChange={e => setRouteForm({ ...routeForm, evening_departure_time: e.target.value })} /></F>
                    </div>
                  </div>

                  <div className="col-span-2 border-t pt-2 mt-1">
                    <p className="text-xs font-semibold text-gray-400 mb-2">Route Details</p>
                    <div className="grid grid-cols-2 gap-2">
                      <F label="Total Distance (km)"><input type="number" step="0.1" className={inp} placeholder="12.5" value={routeForm.total_distance_km} onChange={e => setRouteForm({ ...routeForm, total_distance_km: e.target.value })} /></F>
                      <F label="Est. Duration (mins)"><input type="number" className={inp} placeholder="45" value={routeForm.estimated_duration_minutes} onChange={e => setRouteForm({ ...routeForm, estimated_duration_minutes: e.target.value })} /></F>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 mt-3 pt-2 border-t">
                  <button onClick={handleSaveRoute} disabled={routeSaving} className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-60">
                    {routeSaving ? 'Saving…' : 'Save Route'}
                  </button>
                  <button onClick={() => setShowRouteForm(false)} className="rounded border px-4 py-1.5 text-sm hover:bg-gray-50">Cancel</button>
                </div>
              </div>
            )}

            {loading ? <p className="text-center text-gray-400 py-8 text-sm">Loading…</p> : (
              <div className="space-y-2">
                {routes.length === 0 && <p className="text-center py-8 text-gray-400 text-sm">No routes configured</p>}
                {routes.map(route => (
                  <div
                    key={route.id}
                    className={`rounded-xl border p-3 transition hover:shadow ${selectedRoute?.id === route.id ? 'border-blue-500 bg-blue-50' : 'bg-white'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm">{route.name}</div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          {ROUTE_TYPES.find(t => t.value === route.route_type)?.label ?? route.route_type}
                          {' · '}{route.stops.length} stop{route.stops.length !== 1 ? 's' : ''}
                          {route.total_distance_km ? ` · ${route.total_distance_km} km` : ''}
                        </div>
                        {route.starting_point_name && (
                          <div className="text-xs text-gray-400 mt-1">
                            📍 {route.starting_point_name} → {route.ending_point_name || 'School'}
                          </div>
                        )}
                        {route.morning_departure_time && (
                          <div className="text-xs text-amber-600 mt-0.5">
                            🌅 Departs {route.morning_departure_time} → arrives {route.school_arrival_time || '?'}
                          </div>
                        )}
                        {route.evening_departure_time && (
                          <div className="text-xs text-indigo-600 mt-0.5">
                            🌆 School departs {route.evening_departure_time}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-1 ml-2 flex-shrink-0">
                        <button onClick={() => openRouteForm(route)} className="text-xs text-blue-500 hover:underline">Edit</button>
                        <button onClick={() => handleDeleteRoute(route.id)} className="text-xs text-red-500 hover:underline">Del</button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-xs ${route.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {route.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <button
                        onClick={() => { setSelectedRoute(selectedRoute?.id === route.id ? null : route); setShowStopForm(false); }}
                        className={`rounded px-3 py-1 text-xs font-medium transition ${
                          selectedRoute?.id === route.id
                            ? 'bg-blue-600 text-white'
                            : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
                        }`}>
                        {selectedRoute?.id === route.id ? '✓ Managing Stops' : `🚏 Add / View Stops (${route.stops.length})`}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Stops detail panel */}
          <div className="lg:col-span-3">
            {!selectedRoute ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-400 text-sm border-2 border-dashed rounded-xl">
                <span className="text-4xl mb-3">🚏</span>
                <p className="font-medium text-gray-500">No route selected</p>
                <p className="text-xs mt-1 text-center px-6">Click <strong className="text-blue-600">Add / View Stops</strong> on any route card on the left to manage its pickup and drop points</p>
              </div>
            ) : (() => {
              // morning: sorted ascending (stop 1 → last stop → school)
              // evening: reversed (school → last stop → stop 1 → home)
              const morningStops = [...selectedRoute.stops].sort((a, b) => a.stop_order - b.stop_order);
              const eveningStops = [...morningStops].reverse();
              const displayStops = stopsView === 'morning' ? morningStops : eveningStops;
              const nextOrder = morningStops.length > 0 ? morningStops[morningStops.length - 1].stop_order + 1 : 1;

              return (
                <div className="rounded-xl border bg-white shadow-sm p-4">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-semibold">{selectedRoute.name}</h3>
                      <p className="text-xs text-gray-400">{selectedRoute.stops.length} stops · same stops serve both directions</p>
                    </div>
                    <button
                      onClick={() => { setShowStopForm(!showStopForm); setStopForm({ ...EMPTY_STOP, stop_order: nextOrder }); }}
                      className="rounded bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700">
                      + Add Stop
                    </button>
                  </div>

                  {/* Morning / Evening toggle */}
                  <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 w-fit">
                    <button
                      onClick={() => setStopsView('morning')}
                      className={`px-4 py-1.5 rounded-md text-xs font-medium transition ${
                        stopsView === 'morning' ? 'bg-amber-500 text-white shadow' : 'text-gray-600 hover:bg-gray-200'
                      }`}>
                      🌅 Morning — Home → School
                    </button>
                    <button
                      onClick={() => setStopsView('evening')}
                      className={`px-4 py-1.5 rounded-md text-xs font-medium transition ${
                        stopsView === 'evening' ? 'bg-indigo-600 text-white shadow' : 'text-gray-600 hover:bg-gray-200'
                      }`}>
                      🌆 Evening — School → Home
                    </button>
                  </div>

                  {/* Direction banner */}
                  {stopsView === 'morning' ? (
                    <div className="mb-3 flex items-center gap-2 text-xs bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                      <span className="text-amber-600 font-semibold">Morning route:</span>
                      <span className="text-gray-600">
                        {selectedRoute.starting_point_name || 'Starting Point'}
                        {' → '}
                        {morningStops.map(s => s.name).join(' → ')}
                        {morningStops.length > 0 && (' → ' + (selectedRoute.ending_point_name || 'School'))}
                      </span>
                    </div>
                  ) : (
                    <div className="mb-3 flex items-center gap-2 text-xs bg-indigo-50 border border-indigo-200 rounded-lg px-3 py-2">
                      <span className="text-indigo-600 font-semibold">Evening route (reversed):</span>
                      <span className="text-gray-600">
                        {selectedRoute.ending_point_name || 'School'}
                        {' → '}
                        {eveningStops.map(s => s.name).join(' → ')}
                        {eveningStops.length > 0 && (' → ' + (selectedRoute.starting_point_name || 'Origin'))}
                      </span>
                    </div>
                  )}

                  {/* Add stop form */}
                  {showStopForm && (
                    <div className="mb-4 rounded-lg bg-gray-50 p-3 border">
                      <p className="text-xs font-semibold text-gray-600 mb-1">New Pickup / Drop Point</p>
                      <p className="text-xs text-gray-400 mb-2">Each stop is used for both morning pickup (ascending order) and evening drop (reverse order).</p>
                      <div className="grid grid-cols-2 gap-2">
                        <F label="Stop Name *"><input className={inp} placeholder="e.g. Gandhi Nagar Colony" value={stopForm.name} onChange={e => setStopForm({ ...stopForm, name: e.target.value })} /></F>
                        <F label="Order (Morning Seq.) *">
                          <input type="number" className={inp} value={stopForm.stop_order} onChange={e => setStopForm({ ...stopForm, stop_order: parseInt(e.target.value) || 1 })} />
                          <p className="text-xs text-gray-400 mt-0.5">1 = first pickup in morning / last drop in evening</p>
                        </F>
                        <F label="Address" span={2}><input className={inp} placeholder="Full street address" value={stopForm.address} onChange={e => setStopForm({ ...stopForm, address: e.target.value })} /></F>
                        <F label="Landmark"><input className={inp} placeholder="Nearby landmark" value={stopForm.landmark} onChange={e => setStopForm({ ...stopForm, landmark: e.target.value })} /></F>
                        <F label="Fare (₹)"><input type="number" className={inp} placeholder="0" value={stopForm.fare} onChange={e => setStopForm({ ...stopForm, fare: parseInt(e.target.value) || 0 })} /></F>
                        <F label="🌅 Morning Pickup Time">
                          <input type="time" className={inp} value={stopForm.pickup_time} onChange={e => setStopForm({ ...stopForm, pickup_time: e.target.value })} />
                          <p className="text-xs text-gray-400 mt-0.5">When bus arrives here going to school</p>
                        </F>
                        <F label="🌆 Evening Drop Time">
                          <input type="time" className={inp} value={stopForm.drop_time} onChange={e => setStopForm({ ...stopForm, drop_time: e.target.value })} />
                          <p className="text-xs text-gray-400 mt-0.5">When bus arrives here coming from school</p>
                        </F>
                        <F label="GPS Latitude"><input type="number" step="0.0000001" className={inp} placeholder="12.9716" value={stopForm.latitude} onChange={e => setStopForm({ ...stopForm, latitude: e.target.value })} /></F>
                        <F label="GPS Longitude"><input type="number" step="0.0000001" className={inp} placeholder="77.5946" value={stopForm.longitude} onChange={e => setStopForm({ ...stopForm, longitude: e.target.value })} /></F>
                      </div>
                      <div className="flex gap-2 mt-2">
                        <button onClick={handleAddStop} disabled={stopSaving} className="rounded bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700 disabled:opacity-60">
                          {stopSaving ? 'Adding…' : 'Add Stop'}
                        </button>
                        <button onClick={() => setShowStopForm(false)} className="rounded border px-3 py-1.5 text-xs hover:bg-gray-50">Cancel</button>
                      </div>
                    </div>
                  )}

                  {/* Stops list */}
                  {selectedRoute.stops.length === 0 ? (
                    <p className="text-center text-gray-400 py-6 text-sm">No stops yet — add one above</p>
                  ) : (
                    <div className="space-y-2">
                      {displayStops.map((s, idx) => {
                        const seqNum = idx + 1;
                        const isFirst = idx === 0;
                        const isLast = idx === displayStops.length - 1;
                        const bgColor = stopsView === 'morning' ? 'bg-amber-100 text-amber-700' : 'bg-indigo-100 text-indigo-700';
                        return (
                          <div key={s.id} className="flex items-start gap-3 rounded-lg border p-3 hover:bg-gray-50">
                            {/* Sequence indicator */}
                            <div className="flex flex-col items-center flex-shrink-0">
                              <span className={`w-7 h-7 rounded-full ${bgColor} flex items-center justify-center text-xs font-bold`}>
                                {seqNum}
                              </span>
                              {!isLast && <div className="w-0.5 h-4 bg-gray-200 mt-1" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm">{s.name}</span>
                                {isFirst && stopsView === 'morning' && (
                                  <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">First Pickup</span>
                                )}
                                {isLast && stopsView === 'morning' && (
                                  <span className="text-xs bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded-full">Last Pickup → School</span>
                                )}
                                {isFirst && stopsView === 'evening' && (
                                  <span className="text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full">First Drop (from School)</span>
                                )}
                                {isLast && stopsView === 'evening' && (
                                  <span className="text-xs bg-violet-100 text-violet-700 px-1.5 py-0.5 rounded-full">Last Drop</span>
                                )}
                              </div>
                              {s.address && <div className="text-xs text-gray-500 truncate mt-0.5">{s.address}</div>}
                              {s.landmark && <div className="text-xs text-gray-400">📌 {s.landmark}</div>}
                              <div className="flex flex-wrap gap-3 mt-1">
                                {stopsView === 'morning'
                                  ? s.pickup_time && <span className="text-xs text-amber-600 font-medium">🌅 {s.pickup_time}</span>
                                  : s.drop_time && <span className="text-xs text-indigo-600 font-medium">🌆 {s.drop_time}</span>
                                }
                                {!stopsView || stopsView === 'morning' ? null : null}
                                {s.fare > 0 && <span className="text-xs text-gray-500">₹{s.fare}</span>}
                                {s.latitude && s.longitude && (
                                  <a href={mapsLink(s.latitude, s.longitude)} target="_blank" rel="noreferrer" className="text-xs text-blue-500 hover:underline">📍 Map</a>
                                )}
                              </div>
                            </div>
                            <button onClick={() => handleDeleteStop(selectedRoute.id, s.id)} className="text-xs text-red-500 hover:underline flex-shrink-0 mt-0.5">Remove</button>
                          </div>
                        );
                      })}
                      {/* Terminal node */}
                      <div className="flex items-center gap-3 pl-3">
                        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-sm ${
                          stopsView === 'morning' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                        }`}>
                          {stopsView === 'morning' ? '🏫' : '🏠'}
                        </span>
                        <span className="text-xs text-gray-500 font-medium">
                          {stopsView === 'morning'
                            ? (selectedRoute.ending_point_name || 'School') + (selectedRoute.school_arrival_time ? ` (arrives ${selectedRoute.school_arrival_time})` : '')
                            : (selectedRoute.starting_point_name || 'Origin / Depot')}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* ═══════════════ GPS TRACKING TAB ═══════════════ */}
      {tab === 'gps' && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-700">Fleet GPS Tracking</h3>
              <p className="text-xs text-gray-400 mt-0.5">Real-time vehicle locations — {fleet.filter(hasGPS).length} of {fleet.length} vehicles have GPS data</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowGPSForm(true)} className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50">
                📍 Manual Ping
              </button>
              <button onClick={loadFleet} className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700">
                🔄 Refresh
              </button>
            </div>
          </div>

          {/* Manual GPS ping form */}
          {showGPSForm && (
            <div className="mb-4 rounded-xl border bg-white p-4 shadow-sm">
              <h4 className="font-semibold text-sm mb-3">Manual GPS Update</h4>
              <div className="grid grid-cols-3 gap-3">
                <F label="Vehicle">
                  <select className={inp} value={gpsVehicleId} onChange={e => { setGpsVehicleId(e.target.value); if (e.target.value) loadGPSHistory(e.target.value); }}>
                    <option value="">Select vehicle…</option>
                    {vehicles.map(v => <option key={v.id} value={v.id}>{v.registration_number}</option>)}
                  </select>
                </F>
                <F label="Latitude"><input type="number" step="0.0000001" className={inp} placeholder="12.9716" value={gpsForm.latitude} onChange={e => setGpsForm({ ...gpsForm, latitude: e.target.value })} /></F>
                <F label="Longitude"><input type="number" step="0.0000001" className={inp} placeholder="77.5946" value={gpsForm.longitude} onChange={e => setGpsForm({ ...gpsForm, longitude: e.target.value })} /></F>
                <F label="Speed (km/h)"><input type="number" className={inp} placeholder="0" value={gpsForm.speed_kmph} onChange={e => setGpsForm({ ...gpsForm, speed_kmph: e.target.value })} /></F>
                <F label="Heading (°)"><input type="number" className={inp} placeholder="0–360" value={gpsForm.heading_degrees} onChange={e => setGpsForm({ ...gpsForm, heading_degrees: e.target.value })} /></F>
              </div>
              <div className="flex gap-2 mt-3">
                <button onClick={handleManualGPS} className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700">Update GPS</button>
                <button onClick={() => setShowGPSForm(false)} className="rounded border px-4 py-1.5 text-sm hover:bg-gray-50">Cancel</button>
              </div>
            </div>
          )}

          {/* Fleet locations grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {fleet.length === 0 && !loading && (
              <div className="col-span-3 text-center py-10 text-gray-400">No vehicle data available</div>
            )}
            {fleet.map(v => (
              <div key={v.vehicle_id} className="rounded-xl border bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="font-semibold font-mono">{v.registration_number}</div>
                    <div className="text-xs text-gray-400 capitalize">{v.vehicle_type}</div>
                  </div>
                  {statusBadge(v.vehicle_status)}
                </div>
                {v.driver_name && (
                  <div className="text-xs text-gray-600 mb-2">👤 {v.driver_name} {v.driver_phone ? `· ${v.driver_phone}` : ''}</div>
                )}
                {hasGPS(v) ? (
                  <>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-2 text-xs">
                      <div className="flex items-center gap-1 text-green-700 font-medium mb-1">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse inline-block" /> Last Known Location
                      </div>
                      <div className="text-gray-600">Lat: {v.current_latitude?.toFixed(6)}</div>
                      <div className="text-gray-600">Lng: {v.current_longitude?.toFixed(6)}</div>
                      {v.last_gps_update && (
                        <div className="text-gray-400 mt-1">Updated: {formatDateTime(v.last_gps_update)}</div>
                      )}
                    </div>
                    <a href={mapsLink(v.current_latitude!, v.current_longitude!)} target="_blank" rel="noreferrer"
                      className="mt-2 flex items-center justify-center gap-1 text-xs text-blue-600 hover:underline border border-blue-200 rounded py-1">
                      🗺️ Open in Google Maps
                    </a>
                  </>
                ) : (
                  <div className="bg-gray-50 border rounded-lg p-2 text-xs text-gray-400 text-center">No GPS data yet</div>
                )}
                <button
                  onClick={() => { setGpsVehicleId(v.vehicle_id); loadGPSHistory(v.vehicle_id); }}
                  className="mt-2 text-xs text-blue-500 hover:underline w-full text-center">
                  View History
                </button>
              </div>
            ))}
          </div>

          {/* GPS History for selected vehicle */}
          {gpsVehicleId && gpsHistory.length > 0 && (
            <div className="rounded-xl border bg-white shadow-sm">
              <div className="px-4 py-3 border-b">
                <h4 className="font-semibold text-sm">GPS History — {fleet.find(v => v.vehicle_id === gpsVehicleId)?.registration_number ?? gpsVehicleId.slice(0, 8)}</h4>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead className="bg-gray-50 text-gray-500 uppercase">
                    <tr>
                      {['Time', 'Lat', 'Long', 'Speed', 'Heading', 'Source', 'Map'].map(h => (
                        <th key={h} className="px-3 py-2 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {gpsHistory.map(g => (
                      <tr key={g.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 whitespace-nowrap">{formatDateTime(g.recorded_at)}</td>
                        <td className="px-3 py-2 font-mono">{Number(g.latitude).toFixed(6)}</td>
                        <td className="px-3 py-2 font-mono">{Number(g.longitude).toFixed(6)}</td>
                        <td className="px-3 py-2">{g.speed_kmph != null ? `${g.speed_kmph} km/h` : '—'}</td>
                        <td className="px-3 py-2">{g.heading_degrees != null ? `${g.heading_degrees}°` : '—'}</td>
                        <td className="px-3 py-2 capitalize">{g.source.replace('_', ' ')}</td>
                        <td className="px-3 py-2">
                          <a href={mapsLink(Number(g.latitude), Number(g.longitude))} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">📍</a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════ STUDENT ASSIGNMENTS TAB ═══════════════ */}
      {tab === 'students' && (
        <div>
          <div className="mb-4 text-sm text-gray-500 bg-blue-50 border border-blue-200 rounded-lg p-3">
            ℹ️ Student transport assignments link a student to a specific route and stop for the academic year.
            Subscription type: <strong>Both</strong> = morning pickup + evening drop, <strong>Pickup</strong> = morning only, <strong>Drop</strong> = evening only.
          </div>
          <div className="overflow-x-auto rounded-xl border bg-white shadow-sm">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  {['Student ID', 'Route', 'Stop', 'Subscription', 'Academic Year', 'Status'].map(h => (
                    <th key={h} className="px-4 py-3 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {students.length === 0 ? (
                  <tr><td colSpan={6} className="text-center py-10 text-gray-400">No student transport assignments</td></tr>
                ) : students.map(s => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs">{s.student_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3 text-xs">{routes.find(r => r.id === s.route_id)?.name ?? s.route_id.slice(0, 8) + '…'}</td>
                    <td className="px-4 py-3 text-xs font-mono">{s.stop_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${
                        s.subscription_type === 'both' ? 'bg-blue-100 text-blue-700' :
                        s.subscription_type === 'pickup' ? 'bg-amber-100 text-amber-700' : 'bg-purple-100 text-purple-700'
                      }`}>{s.subscription_type}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{s.academic_year_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {s.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═══════════════ MAINTENANCE TAB ═══════════════ */}
      {tab === 'maintenance' && (
        <div>
          <div className="mb-4 flex items-center gap-3">
            <select className="border rounded px-3 py-2 text-sm" value={selectedVehicle?.id ?? ''}
              onChange={e => {
                const v = vehicles.find(v => v.id === e.target.value) ?? null;
                setSelectedVehicle(v);
                if (v) loadMaintenance(v.id);
              }}>
              <option value="">Select vehicle…</option>
              {vehicles.map(v => <option key={v.id} value={v.id}>{v.registration_number} — {v.make} {v.model}</option>)}
            </select>
            {selectedVehicle && (
              <button onClick={() => setShowMaintForm(true)} className="rounded-lg bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">
                + Add Record
              </button>
            )}
          </div>

          {selectedVehicle && showMaintForm && (
            <div className="mb-4 rounded-xl border bg-white p-4 shadow-sm">
              <h4 className="font-semibold text-sm mb-3">Add Maintenance Record — {selectedVehicle.registration_number}</h4>
              <div className="grid grid-cols-3 gap-3">
                <F label="Type *"><input className={inp} placeholder="e.g. Oil Change, Tyre" value={maintForm.maintenance_type} onChange={e => setMaintForm({ ...maintForm, maintenance_type: e.target.value })} /></F>
                <F label="Date *"><input type="date" className={inp} value={maintForm.maintenance_date} onChange={e => setMaintForm({ ...maintForm, maintenance_date: e.target.value })} /></F>
                <F label="Status">
                  <select className={inp} value={maintForm.status} onChange={e => setMaintForm({ ...maintForm, status: e.target.value })}>
                    {['completed', 'scheduled', 'in_progress'].map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </F>
                <F label="Cost (₹)"><input type="number" className={inp} value={maintForm.cost} onChange={e => setMaintForm({ ...maintForm, cost: parseInt(e.target.value) || 0 })} /></F>
                <F label="Vendor"><input className={inp} placeholder="Vendor / Garage name" value={maintForm.vendor_name} onChange={e => setMaintForm({ ...maintForm, vendor_name: e.target.value })} /></F>
                <F label="Odometer (km)"><input type="number" className={inp} value={maintForm.odometer_reading} onChange={e => setMaintForm({ ...maintForm, odometer_reading: e.target.value })} /></F>
                <F label="Next Due Date"><input type="date" className={inp} value={maintForm.next_due_date} onChange={e => setMaintForm({ ...maintForm, next_due_date: e.target.value })} /></F>
                <F label="Description" span={2}><input className={inp} placeholder="Details" value={maintForm.description} onChange={e => setMaintForm({ ...maintForm, description: e.target.value })} /></F>
                <F label="Notes" span={2}><input className={inp} placeholder="Internal notes" value={maintForm.notes} onChange={e => setMaintForm({ ...maintForm, notes: e.target.value })} /></F>
              </div>
              <div className="flex gap-2 mt-3">
                <button onClick={handleAddMaintenance} className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700">Save</button>
                <button onClick={() => setShowMaintForm(false)} className="rounded border px-4 py-1.5 text-sm hover:bg-gray-50">Cancel</button>
              </div>
            </div>
          )}

          {selectedVehicle && (
            <div className="overflow-x-auto rounded-xl border bg-white shadow-sm">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                  <tr>{['Date', 'Type', 'Status', 'Cost ₹', 'Vendor', 'Odometer', 'Next Due', 'Notes'].map(h => <th key={h} className="px-3 py-3 text-left">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y">
                  {maintenance.length === 0 ? (
                    <tr><td colSpan={8} className="text-center py-8 text-gray-400">No maintenance records</td></tr>
                  ) : maintenance.map(m => (
                    <tr key={m.id} className="hover:bg-gray-50">
                      <td className="px-3 py-3 whitespace-nowrap">{m.maintenance_date}</td>
                      <td className="px-3 py-3">{m.maintenance_type}</td>
                      <td className="px-3 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs ${m.status === 'completed' ? 'bg-green-100 text-green-700' : m.status === 'scheduled' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'}`}>{m.status}</span>
                      </td>
                      <td className="px-3 py-3 text-right font-medium">₹{(m.cost / 100).toFixed(0)}</td>
                      <td className="px-3 py-3">{m.vendor_name ?? '—'}</td>
                      <td className="px-3 py-3">{m.odometer_reading ? `${m.odometer_reading} km` : '—'}</td>
                      <td className="px-3 py-3">{m.next_due_date ?? '—'}</td>
                      <td className="px-3 py-3 text-xs text-gray-400">{m.notes ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════ FUEL LOGS TAB ═══════════════ */}
      {tab === 'fuel' && (
        <div>
          <div className="mb-4 flex items-center gap-3">
            <select className="border rounded px-3 py-2 text-sm" value={selectedVehicle?.id ?? ''}
              onChange={e => {
                const v = vehicles.find(v => v.id === e.target.value) ?? null;
                setSelectedVehicle(v);
                if (v) loadFuelLogs(v.id);
              }}>
              <option value="">Select vehicle…</option>
              {vehicles.map(v => <option key={v.id} value={v.id}>{v.registration_number} — {v.make} {v.model}</option>)}
            </select>
            {selectedVehicle && (
              <button onClick={() => setShowFuelForm(true)} className="rounded-lg bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">
                + Add Fuel Log
              </button>
            )}
          </div>

          {selectedVehicle && showFuelForm && (
            <div className="mb-4 rounded-xl border bg-white p-4 shadow-sm">
              <h4 className="font-semibold text-sm mb-3">Add Fuel Log — {selectedVehicle.registration_number}</h4>
              <div className="grid grid-cols-3 gap-3">
                <F label="Date *"><input type="date" className={inp} value={fuelForm.fuel_date} onChange={e => setFuelForm({ ...fuelForm, fuel_date: e.target.value })} /></F>
                <F label="Qty (Litres)"><input type="number" step="0.01" className={inp} placeholder="0.00" value={fuelForm.fuel_quantity} onChange={e => setFuelForm({ ...fuelForm, fuel_quantity: e.target.value })} /></F>
                <F label="Cost (₹)"><input type="number" className={inp} placeholder="0" value={fuelForm.fuel_cost} onChange={e => setFuelForm({ ...fuelForm, fuel_cost: parseInt(e.target.value) || 0 })} /></F>
                <F label="Odometer (km)"><input type="number" className={inp} placeholder="km reading" value={fuelForm.odometer_reading} onChange={e => setFuelForm({ ...fuelForm, odometer_reading: e.target.value })} /></F>
                <F label="Pump Name"><input className={inp} placeholder="Pump / station name" value={fuelForm.pump_name} onChange={e => setFuelForm({ ...fuelForm, pump_name: e.target.value })} /></F>
              </div>
              <div className="flex gap-2 mt-3">
                <button onClick={handleAddFuelLog} className="rounded bg-blue-600 px-4 py-1.5 text-sm text-white hover:bg-blue-700">Save</button>
                <button onClick={() => setShowFuelForm(false)} className="rounded border px-4 py-1.5 text-sm hover:bg-gray-50">Cancel</button>
              </div>
            </div>
          )}

          {selectedVehicle && (
            <div className="overflow-x-auto rounded-xl border bg-white shadow-sm">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                  <tr>{['Date', 'Quantity (L)', 'Cost ₹', 'Odometer', 'Pump'].map(h => <th key={h} className="px-3 py-3 text-left">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y">
                  {fuelLogs.length === 0 ? (
                    <tr><td colSpan={5} className="text-center py-8 text-gray-400">No fuel logs</td></tr>
                  ) : fuelLogs.map(f => (
                    <tr key={f.id} className="hover:bg-gray-50">
                      <td className="px-3 py-3 whitespace-nowrap">{f.fuel_date}</td>
                      <td className="px-3 py-3">{f.fuel_quantity != null ? f.fuel_quantity : '—'} L</td>
                      <td className="px-3 py-3 font-medium text-right">₹{(f.fuel_cost / 100).toFixed(0)}</td>
                      <td className="px-3 py-3">{f.odometer_reading ? `${f.odometer_reading} km` : '—'}</td>
                      <td className="px-3 py-3">{f.pump_name ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TransportPage;
