import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import { calendarService } from '@/services/misc.service';
import { Loading } from '@/components/Loading';
import { COLORS, STALE_15MIN } from '@/constants';

export default function CalendarScreen() {
  const [currentMonth, setCurrentMonth] = useState(dayjs());

  const start = currentMonth.startOf('month').format('YYYY-MM-DD');
  const end   = currentMonth.endOf('month').format('YYYY-MM-DD');

  const { data: events, isLoading, refetch, isRefetching } = useQuery({
    queryKey:  ['calendar', start, end],
    queryFn:   () => calendarService.getEvents(start, end),
    staleTime: STALE_15MIN,
  });

  const { data: holidays } = useQuery({
    queryKey:  ['holidays'],
    queryFn:   () => calendarService.getHolidays(),
    staleTime: STALE_15MIN,
  });

  const eventsByDate: Record<string, any[]> = {};
  (events ?? []).forEach((e: any) => {
    const d = dayjs(e.startDate ?? e.date).format('YYYY-MM-DD');
    if (!eventsByDate[d]) eventsByDate[d] = [];
    eventsByDate[d].push(e);
  });
  (holidays ?? []).forEach((h: any) => {
    const d = dayjs(h.date).format('YYYY-MM-DD');
    if (!eventsByDate[d]) eventsByDate[d] = [];
    eventsByDate[d].push({ ...h, isHoliday: true });
  });

  const daysInMonth  = currentMonth.daysInMonth();
  const startDow     = currentMonth.startOf('month').day(); // 0=Sun
  const days         = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const blanks       = Array.from({ length: startDow }, (_, i) => i);

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <View className="flex-row items-center justify-between">
          <TouchableOpacity onPress={() => setCurrentMonth((m) => m.subtract(1, 'month'))}>
            <Ionicons name="chevron-back" size={22} color={COLORS.gray700} />
          </TouchableOpacity>
          <Text className="text-gray-800 text-lg font-bold">{currentMonth.format('MMMM YYYY')}</Text>
          <TouchableOpacity onPress={() => setCurrentMonth((m) => m.add(1, 'month'))}>
            <Ionicons name="chevron-forward" size={22} color={COLORS.gray700} />
          </TouchableOpacity>
        </View>
      </View>
      <ScrollView
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ padding: 16 }}
      >
        {/* Day labels */}
        <View className="flex-row mb-2">
          {['Su','Mo','Tu','We','Th','Fr','Sa'].map((d) => (
            <Text key={d} className="flex-1 text-center text-gray-400 text-xs font-medium">{d}</Text>
          ))}
        </View>
        {/* Calendar grid */}
        <View className="flex-row flex-wrap">
          {blanks.map((b) => <View key={`b${b}`} style={{ width: `${100/7}%` }} />)}
          {days.map((day) => {
            const dateStr = currentMonth.date(day).format('YYYY-MM-DD');
            const hasEvent   = !!eventsByDate[dateStr]?.length;
            const isHoliday  = eventsByDate[dateStr]?.some((e) => e.isHoliday);
            const isToday    = dateStr === dayjs().format('YYYY-MM-DD');
            return (
              <View key={day} style={{ width: `${100/7}%` }} className="items-center mb-3">
                <View className={`w-8 h-8 rounded-full items-center justify-center ${isToday ? 'bg-primary-700' : ''}`}>
                  <Text className={`text-sm ${isToday ? 'text-white font-bold' : isHoliday ? 'text-red-500' : 'text-gray-700'}`}>{day}</Text>
                </View>
                {hasEvent && <View className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-0.5" />}
              </View>
            );
          })}
        </View>

        {/* Event list */}
        {isLoading ? <Loading /> : (
          <View className="mt-4">
            <Text className="text-gray-700 font-semibold mb-3">Events this month</Text>
            {Object.entries(eventsByDate).sort().map(([date, evts]) => (
              <View key={date} className="mb-3">
                <Text className="text-primary-600 text-xs font-medium mb-1">{dayjs(date).format('ddd, DD MMM')}</Text>
                {evts.map((e, idx) => (
                  <View key={idx} className={`rounded-xl p-3 mb-1 ${e.isHoliday ? 'bg-red-50' : 'bg-white shadow-sm'}`}>
                    <Text className={`font-medium text-sm ${e.isHoliday ? 'text-red-700' : 'text-gray-800'}`}>{e.title ?? e.name}</Text>
                    {e.description && <Text className="text-gray-400 text-xs mt-0.5" numberOfLines={1}>{e.description}</Text>}
                  </View>
                ))}
              </View>
            ))}
            {Object.keys(eventsByDate).length === 0 && (
              <View className="items-center py-8">
                <Text className="text-gray-400">No events this month</Text>
              </View>
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
