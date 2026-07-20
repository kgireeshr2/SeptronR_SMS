import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { staffService } from '@/services/staff.service';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge } from '@/components/Badge';
import { COLORS } from '@/constants';

export default function StaffDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const { data: staff, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['staff', id],
    queryFn:  () => staffService.get(id as string),
  });

  if (isLoading) return <Loading fullScreen />;
  if (isError || !staff) return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <ScrollView refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}>
        <View className="bg-primary-800 pt-4 pb-10 px-4">
          <TouchableOpacity onPress={() => router.back()} className="mb-4">
            <Ionicons name="arrow-back" size={22} color="#fff" />
          </TouchableOpacity>
          <View className="items-center">
            <View className="w-20 h-20 rounded-full bg-blue-200 items-center justify-center mb-2">
              <Text className="text-blue-800 text-3xl font-bold">{(staff.full_name ?? '').charAt(0)}</Text>
            </View>
            <Text className="text-white text-xl font-bold">{staff.full_name}</Text>
            <Text className="text-blue-200 text-sm">{staff.designation_name}</Text>
            <Badge label={staff.is_active ? 'active' : 'inactive'} variant={staff.is_active ? 'success' : 'default'} />
          </View>
        </View>
        <View className="bg-white rounded-2xl mx-4 -mt-4 p-4 shadow-sm">
          <Text className="text-gray-700 font-semibold mb-3">Details</Text>
          <InfoRow label="Employee ID"  value={staff.employee_id}          />
          <InfoRow label="Department"   value={staff.department_name ?? ''}  />
          <InfoRow label="Email"        value={staff.email}                  />
          <InfoRow label="Phone"        value={staff.phone ?? ''}            />
        </View>
        <View className="bg-white rounded-2xl mx-4 mt-3 p-4 shadow-sm mb-6">
          <Text className="text-gray-700 font-semibold mb-3">Quick Links</Text>
          <View className="flex-row flex-wrap">
            <LinkChip icon="time"    label="Leaves"   onPress={() => router.push('/(app)/leaves/index')} />
            <LinkChip icon="cash"    label="Payroll"  onPress={() => {}} />
            <LinkChip icon="calendar" label="Attendance" onPress={() => router.push('/(app)/attendance/index')} />
          </View>
        </View>
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

function LinkChip({ icon, label, onPress }: { icon: keyof typeof Ionicons.glyphMap; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} className="mr-2 mb-2 flex-row items-center bg-gray-100 rounded-full px-3 py-1.5">
      <Ionicons name={icon} size={14} color={COLORS.primary} />
      <Text className="text-gray-700 text-xs ml-1">{label}</Text>
    </TouchableOpacity>
  );
}
