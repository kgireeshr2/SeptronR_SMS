import React from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { notificationsService } from '@/services/announcements.service';
import { Loading } from '@/components/Loading';
import { AppNotification } from '@/types';
import { COLORS, STALE_5MIN } from '@/constants';

dayjs.extend(relativeTime);

export default function NotificationsScreen() {
  const qc = useQueryClient();

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey:  ['notifications'],
    queryFn:   () => notificationsService.list({ page: 1, page_size: 50 }),
    staleTime: STALE_5MIN,
  });

  const markAllMutation = useMutation({
    mutationFn: notificationsService.markAllRead,
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const renderItem = ({ item }: { item: AppNotification }) => (
    <View className={`mx-4 mb-1.5 rounded-xl p-4 ${item.is_read ? 'bg-white' : 'bg-primary-50 border border-primary-100'}`}>
      <View className="flex-row justify-between items-start">
        <Text className={`flex-1 font-semibold text-sm pr-2 ${item.is_read ? 'text-gray-700' : 'text-primary-900'}`}>{item.title}</Text>
        {!item.is_read && <View className="w-2 h-2 rounded-full bg-primary-600 mt-1" />}
      </View>
      <Text className="text-gray-500 text-sm mt-1">{item.message}</Text>
      <Text className="text-gray-400 text-xs mt-2">{dayjs(item.created_at).fromNow()}</Text>
    </View>
  );

  if (isLoading) return <Loading fullScreen />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100 flex-row justify-between items-center">
        <Text className="text-gray-800 text-xl font-bold">Notifications</Text>
        <TouchableOpacity onPress={() => markAllMutation.mutate()}>
          <Text className="text-primary-600 text-sm">Mark all read</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={data?.items ?? []}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
        ListEmptyComponent={() => (
          <View className="items-center mt-16">
            <Ionicons name="notifications-off-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No notifications</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}
