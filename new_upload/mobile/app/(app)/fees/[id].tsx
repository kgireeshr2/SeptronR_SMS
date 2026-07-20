import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import { feesService } from '@/services/fees.service';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge, feeStatusBadge } from '@/components/Badge';
import { COLORS } from '@/constants';

export default function FeeInvoiceDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const { data: invoice, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['fee-invoice', id],
    queryFn:  () => feesService.getInvoice(id as string),
  });

  if (isLoading) return <Loading fullScreen />;
  if (isError || !invoice) return <ErrorView onRetry={refetch} />;

  const paidPct = (invoice.total_amount ?? 0) > 0
    ? Math.min(100, Math.round(((invoice.paid_amount ?? 0) / (invoice.total_amount ?? 1)) * 100))
    : 0;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <ScrollView refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}>
        {/* Header */}
        <View className="bg-primary-800 pt-4 pb-10 px-4">
          <TouchableOpacity onPress={() => router.back()} className="mb-4">
            <Ionicons name="arrow-back" size={22} color="#fff" />
          </TouchableOpacity>
          <View className="flex-row justify-between items-start">
            <View>
              <Text className="text-white text-xl font-bold">{invoice.student_name}</Text>
              <Text className="text-blue-200 text-sm">Invoice #{invoice.invoice_number}</Text>
              <Text className="text-blue-200 text-xs">Due: {invoice.due_date ? dayjs(invoice.due_date).format('DD MMM YYYY') : '-'}</Text>
            </View>
            <Badge label={invoice.status} variant={feeStatusBadge(invoice.status)} />
          </View>
        </View>

        {/* Summary Card */}
        <View className="bg-white mx-4 -mt-4 rounded-2xl p-4 shadow-sm">
          <View className="flex-row justify-between mb-3">
            <AmountBox label="Total"  amount={invoice.total_amount ?? 0} color={COLORS.gray700} />
            <AmountBox label="Paid"   amount={invoice.paid_amount ?? 0}  color={COLORS.success} />
            <AmountBox label="Due"    amount={invoice.due_amount ?? 0}   color={COLORS.danger}  />
          </View>
          <View className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <View style={{ width: `${paidPct}%`, backgroundColor: COLORS.success }} className="h-full rounded-full" />
          </View>
          <Text className="text-gray-400 text-xs mt-1 text-right">{paidPct}% paid</Text>
        </View>

        {/* Line Items */}
        <View className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-sm mb-4">
          <Text className="text-gray-700 font-semibold mb-3">Line Items</Text>
          {invoice.items?.map((item) => (
            <View key={item.id} className="flex-row justify-between py-2 border-b border-gray-50">
              <Text className="text-gray-600 text-sm flex-1">{item.fee_category_name ?? item.fee_name}</Text>
              <Text className="text-gray-700 text-sm font-medium">₹{item.amount.toLocaleString()}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function AmountBox({ label, amount, color }: { label: string; amount: number; color: string }) {
  return (
    <View className="items-center">
      <Text className="text-gray-400 text-xs mb-1">{label}</Text>
      <Text style={{ color }} className="text-lg font-bold">₹{amount.toLocaleString()}</Text>
    </View>
  );
}
