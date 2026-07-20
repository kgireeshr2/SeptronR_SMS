import React from 'react';
import { View, Text, ScrollView, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { timetableService } from '@/services/timetable.service';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { TimetableSlot } from '@/types';
import { COLORS, STALE_15MIN } from '@/constants';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export default function TimetableScreen() {
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['my-timetable'],
    queryFn:   timetableService.getMyTimetable,
    staleTime: STALE_15MIN,
  });

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  const grouped: Record<string, TimetableSlot[]> = {};
  (data ?? []).forEach((slot) => {
    const day = slot.day_name ?? DAYS[((slot.day_of_week ?? 1) - 1) % 6];
    if (!grouped[day]) grouped[day] = [];
    grouped[day].push(slot);
  });

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">Timetable</Text>
      </View>
      <ScrollView
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ padding: 16 }}
      >
        {DAYS.map((day) => {
          const slots = grouped[day];
          if (!slots?.length) return null;
          return (
            <View key={day} className="mb-4">
              <Text className="text-primary-700 font-semibold mb-2">{day}</Text>
              {slots
                .sort((a, b) => (a.period_number ?? 0) - (b.period_number ?? 0))
                .map((slot) => (
                  <View key={slot.id} className="bg-white rounded-xl p-3 mb-1.5 flex-row items-center shadow-sm">
                    <View className="w-10 h-10 rounded-xl bg-primary-50 items-center justify-center mr-3">
                      <Text className="text-primary-700 font-bold text-xs">P{slot.period_number}</Text>
                    </View>
                    <View className="flex-1">
                      <Text className="text-gray-800 font-semibold text-sm">{slot.subject_name}</Text>
                      <Text className="text-gray-400 text-xs">{slot.staff_name}</Text>
                    </View>
                    <View className="items-end">
                      <Text className="text-gray-500 text-xs">{slot.start_time}</Text>
                      <Text className="text-gray-400 text-xs">{slot.end_time}</Text>
                    </View>
                  </View>
                ))}
            </View>
          );
        })}
        {Object.keys(grouped).length === 0 && (
          <View className="items-center mt-16">
            <Ionicons name="calendar-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No timetable assigned</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
