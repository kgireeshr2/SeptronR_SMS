import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import api from '@/services/api';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { COLORS, STALE_5MIN } from '@/constants';

export default function ReportsScreen() {
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['reports-list'],
    queryFn:   () => api.get('/reports').then((r) => r.data),
    staleTime: STALE_5MIN,
  });

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  const reports = (data?.reports ?? data ?? []) as Array<{ id: string | number; name: string; description?: string; type?: string }>;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">Reports</Text>
      </View>
      <ScrollView
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ padding: 16 }}
      >
        {reports.length > 0 ? (
          reports.map((r) => (
            <TouchableOpacity key={r.id} className="bg-white rounded-xl p-4 mb-2 flex-row items-center shadow-sm">
              <View className="w-10 h-10 rounded-xl bg-indigo-50 items-center justify-center mr-3">
                <Ionicons name="bar-chart-outline" size={20} color="#6366f1" />
              </View>
              <View className="flex-1">
                <Text className="text-gray-800 font-semibold text-sm">{r.name}</Text>
                {r.description && <Text className="text-gray-400 text-xs mt-0.5" numberOfLines={1}>{r.description}</Text>}
              </View>
              <Ionicons name="download-outline" size={18} color={COLORS.gray500} />
            </TouchableOpacity>
          ))
        ) : (
          <View className="items-center mt-16">
            <Ionicons name="document-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No reports available</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
