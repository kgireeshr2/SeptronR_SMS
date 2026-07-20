import React from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import { announcementsService } from '@/services/announcements.service';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Announcement } from '@/types';
import { COLORS, STALE_5MIN } from '@/constants';

export default function AnnouncementsScreen() {
  const qc = useQueryClient();
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['announcements'],
    queryFn:   () => announcementsService.list({ page: 1, page_size: 50 }),
    staleTime: STALE_5MIN,
  });

  const readMutation = useMutation({
    mutationFn: (id: string) => announcementsService.markRead(id),
    onSuccess:  () => qc.invalidateQueries({ queryKey: ['announcements'] }),
  });

  const renderItem = ({ item }: { item: Announcement }) => (
    <TouchableOpacity
      onPress={() => { if (!item.is_read) readMutation.mutate(item.id); }}
      className={`mx-4 mb-2 rounded-xl p-4 shadow-sm ${item.is_read ? 'bg-white' : 'bg-primary-50 border border-primary-100'}`}
    >
      <View className="flex-row justify-between items-start mb-1">
        <Text className={`flex-1 font-semibold pr-2 ${item.is_read ? 'text-gray-700' : 'text-primary-800'}`}>{item.title}</Text>
        {!item.is_read && <View className="w-2 h-2 rounded-full bg-primary-600 mt-1.5" />}
      </View>
      <Text className="text-gray-500 text-sm" numberOfLines={2}>{item.content}</Text>
      <View className="flex-row justify-between mt-2">
        <Text className="text-gray-400 text-xs">{item.created_by_name}</Text>
        <Text className="text-gray-400 text-xs">{dayjs(item.published_at).fromNow()}</Text>
      </View>
    </TouchableOpacity>
  );

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">Announcements</Text>
      </View>
      <FlatList
        data={data?.items ?? []}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
        ListEmptyComponent={() => (
          <View className="items-center mt-16">
            <Ionicons name="megaphone-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No announcements</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}
