import React from 'react';
import { View, Text, ScrollView, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { transportService } from '@/services/misc.service';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { COLORS, STALE_15MIN } from '@/constants';

export default function TransportScreen() {
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['my-transport'],
    queryFn:   transportService.getMyRoute,
    staleTime: STALE_15MIN,
  });

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">Transport</Text>
      </View>
      <ScrollView
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ padding: 16 }}
      >
        {data ? (
          <View className="bg-white rounded-2xl p-4 shadow-sm">
            <View className="flex-row items-center mb-4">
              <View className="w-12 h-12 rounded-full bg-yellow-100 items-center justify-center mr-3">
                <Ionicons name="bus" size={24} color="#d97706" />
              </View>
              <View>
                <Text className="text-gray-800 font-bold text-base">{data.routeName ?? 'Route'}</Text>
                <Text className="text-gray-400 text-sm">Vehicle: {data.vehicleNumber ?? '—'}</Text>
              </View>
            </View>
            <InfoRow label="Driver"      value={data.driverName   ?? '—'} />
            <InfoRow label="Contact"     value={data.driverPhone  ?? '—'} />
            <InfoRow label="Pickup Stop" value={data.stopName     ?? '—'} />
            <InfoRow label="Pickup Time" value={data.pickupTime   ?? '—'} />
            <InfoRow label="Drop Time"   value={data.dropTime     ?? '—'} />
          </View>
        ) : (
          <View className="items-center mt-16">
            <Ionicons name="bus-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No transport assigned</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row justify-between py-2 border-b border-gray-50">
      <Text className="text-gray-400 text-sm">{label}</Text>
      <Text className="text-gray-700 text-sm font-medium">{value}</Text>
    </View>
  );
}
