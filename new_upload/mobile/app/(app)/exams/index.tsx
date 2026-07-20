import React from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import { examsService } from '@/services/exams.service';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge } from '@/components/Badge';
import { Exam } from '@/types';
import { COLORS, STALE_5MIN } from '@/constants';

export default function ExamsScreen() {
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['exams'],
    queryFn:   () => examsService.list({}),
    staleTime: STALE_5MIN,
  });

  const renderItem = ({ item }: { item: Exam }) => (
    <View className="bg-white mx-4 mb-2 rounded-xl p-4 shadow-sm">
      <View className="flex-row justify-between items-start">
        <View className="flex-1">
          <Text className="text-gray-800 font-semibold">{item.name}</Text>
          <Text className="text-gray-400 text-xs mt-0.5">{item.exam_type_name} · {item.class_name}</Text>
        </View>
        <Badge label={item.status ?? 'draft'} variant={item.status === 'completed' ? 'success' : item.status === 'ongoing' ? 'info' : 'warning'} small />
      </View>
      <View className="flex-row mt-3 space-x-4">
        <View className="flex-row items-center">
          <Ionicons name="calendar-outline" size={13} color={COLORS.gray500} />
          <Text className="text-gray-400 text-xs ml-1">{item.start_date ? dayjs(item.start_date).format('DD MMM') : ''} – {item.end_date ? dayjs(item.end_date).format('DD MMM YYYY') : ''}</Text>
        </View>
      </View>
    </View>
  );

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">Exams</Text>
      </View>
      <FlatList
        data={Array.isArray(data) ? data : (data?.items ?? [])}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
        ListEmptyComponent={() => (
          <View className="items-center mt-16">
            <Ionicons name="trophy-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No exams found</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}
