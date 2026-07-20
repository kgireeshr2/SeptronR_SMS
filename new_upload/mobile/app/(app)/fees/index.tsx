import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import { feesService } from '@/services/fees.service';
import { usePermissions } from '@/hooks/usePermissions';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge, feeStatusBadge } from '@/components/Badge';
import { FeeInvoice } from '@/types';
import { COLORS, PAGE_SIZE, STALE_5MIN } from '@/constants';

export default function FeesScreen() {
  const { isAdmin } = usePermissions();
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['fee-invoices', page],
    queryFn:   () => feesService.getInvoices({ page, page_size: PAGE_SIZE }),
    staleTime: STALE_5MIN,
  });

  const renderItem = ({ item }: { item: FeeInvoice }) => (
    <TouchableOpacity
      onPress={() => router.push(`/(app)/fees/${item.id}`)}
      className="bg-white mx-4 mb-2 rounded-xl p-4 shadow-sm"
    >
      <View className="flex-row justify-between items-start mb-2">
        <View className="flex-1">
          <Text className="text-gray-800 font-semibold text-sm">{item.student_name}</Text>
          <Text className="text-gray-400 text-xs">#{item.invoice_number}</Text>
        </View>
        <Badge label={item.status} variant={feeStatusBadge(item.status)} small />
      </View>
      <View className="flex-row justify-between mt-2">
        <View>
          <Text className="text-gray-400 text-xs">Total</Text>
          <Text className="text-gray-700 font-semibold text-sm">₹{(item.total_amount ?? 0).toLocaleString()}</Text>
        </View>
        <View>
          <Text className="text-gray-400 text-xs">Paid</Text>
          <Text className="text-success font-semibold text-sm">₹{(item.paid_amount ?? 0).toLocaleString()}</Text>
        </View>
        <View>
          <Text className="text-gray-400 text-xs">Due</Text>
          <Text className="text-danger font-semibold text-sm">₹{(item.due_amount ?? 0).toLocaleString()}</Text>
        </View>
        <View>
          <Text className="text-gray-400 text-xs">Due Date</Text>
          <Text className="text-gray-500 text-xs">{item.due_date ? dayjs(item.due_date).format('DD MMM YYYY') : '-'}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <View className="flex-row justify-between items-center">
          <Text className="text-gray-800 text-xl font-bold">Fee Invoices</Text>
          <Text className="text-gray-400 text-sm">{Array.isArray(data) ? data.length : (data?.total ?? 0)} total</Text>
        </View>
      </View>
      <FlatList
        data={Array.isArray(data) ? data : (data?.items ?? [])}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
        ListEmptyComponent={() => (
          <View className="items-center mt-16">
            <Ionicons name="wallet-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No invoices found</Text>
          </View>
        )}
        onEndReached={() => { if (!Array.isArray(data) && data && page < (data.total_pages ?? 0)) setPage((p) => p + 1); }}
        onEndReachedThreshold={0.3}
      />
    </SafeAreaView>
  );
}
