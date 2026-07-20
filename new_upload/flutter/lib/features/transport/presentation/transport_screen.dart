import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/domain/app_role.dart';
import '../application/transport_providers.dart';
import '../domain/transport_models.dart';

class TransportScreen extends ConsumerWidget {
  const TransportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final role = ref.watch(roleProvider);
    final isAdmin = role == AppRole.admin || role == AppRole.superAdmin;

    if (!isAdmin) {
      return Scaffold(
        appBar: AppBar(title: const Text('Transport')),
        body: const _MyRoute(),
      );
    }

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Transport'),
          bottom: const TabBar(
            indicatorColor: Colors.white,
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            tabs: [Tab(text: 'Routes'), Tab(text: 'Vehicles')],
          ),
        ),
        body: const TabBarView(children: [_Routes(), _Vehicles()]),
      ),
    );
  }
}

class _MyRoute extends ConsumerWidget {
  const _MyRoute();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(myTransportProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(myTransportProvider),
      ),
      data: (route) {
        if (route == null) {
          return const EmptyView(
              message: 'No transport route assigned',
              icon: Icons.directions_bus_outlined);
        }
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [_RouteCard(route: route, expanded: true)],
        );
      },
    );
  }
}

class _Routes extends ConsumerWidget {
  const _Routes();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(routesProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(routesProvider),
      ),
      data: (routes) {
        if (routes.isEmpty) {
          return const EmptyView(message: 'No routes configured');
        }
        return ListView(
          padding: const EdgeInsets.all(12),
          children: [for (final r in routes) _RouteCard(route: r)],
        );
      },
    );
  }
}

class _Vehicles extends ConsumerWidget {
  const _Vehicles();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(vehiclesProvider);
    return async.when(
      loading: () => const LoadingView(),
      error: (e, _) => ErrorView(
        message: e.toString(),
        onRetry: () => ref.invalidate(vehiclesProvider),
      ),
      data: (vehicles) {
        if (vehicles.isEmpty) {
          return const EmptyView(message: 'No vehicles');
        }
        return ListView.separated(
          itemCount: vehicles.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (_, i) {
            final v = vehicles[i];
            return ListTile(
              leading: const Icon(Icons.directions_bus, color: AppColors.primary),
              title: Text(v.number ?? v.model ?? 'Vehicle'),
              subtitle: Text([
                if (v.model != null) v.model,
                if (v.capacity != null) 'Seats ${v.capacity}',
                if (v.driverName != null) 'Driver: ${v.driverName}',
              ].whereType<String>().join(' · ')),
            );
          },
        );
      },
    );
  }
}

class _RouteCard extends StatelessWidget {
  const _RouteCard({required this.route, this.expanded = false});
  final TransportRoute route;
  final bool expanded;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.gray200),
      ),
      child: ExpansionTile(
        initiallyExpanded: expanded,
        shape: const Border(),
        leading: const Icon(Icons.route_outlined, color: AppColors.primary),
        title: Text(route.name,
            style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text([
          if (route.vehicleNumber != null) route.vehicleNumber,
          if (route.driverName != null) route.driverName,
        ].whereType<String>().join(' · ')),
        children: [
          if (route.stops.isEmpty)
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('No stops listed',
                  style: TextStyle(color: AppColors.gray500)),
            )
          else
            for (final s in route.stops)
              ListTile(
                dense: true,
                leading: const Icon(Icons.location_on_outlined, size: 20),
                title: Text(s.name),
                trailing: s.time != null
                    ? Text(s.time!,
                        style: const TextStyle(color: AppColors.gray500))
                    : null,
              ),
        ],
      ),
    );
  }
}
