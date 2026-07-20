import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { staffService } from '@/services/staff.service';
import { SearchBar } from '@/components/SearchBar';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge } from '@/components/Badge';
import { Staff } from '@/types';
import { COLORS, PAGE_SIZE, STALE_5MIN } from '@/constants';

export default function StaffScreen() {
  const [search, setSearch] = useState('');
  const [page,   setPage]   = useState(1);

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['staff', search, page],
    queryFn:   () => staffService.list({ page, page_size: PAGE_SIZE, search: search || undefined }),
    staleTime: STALE_5MIN,
  });

  const renderItem = ({ item }: { item: Staff }) => (
    <TouchableOpacity
      onPress={() => router.push(`/(app)/staff/${item.id}`)}
      className="bg-white mx-4 mb-2 rounded-xl p-4 flex-row items-center shadow-sm"
    >
      <View className="w-12 h-12 rounded-full bg-blue-100 items-center justify-center mr-3">
        <Text className="text-blue-700 font-bold text-base">{(item.full_name ?? '').charAt(0)}</Text>
      </View>
      <View className="flex-1">
        <Text className="text-gray-800 font-semibold text-sm">{item.full_name}</Text>
        <Text className="text-gray-400 text-xs mt-0.5">{item.designation_name}</Text>
        <Text className="text-gray-400 text-xs">{item.department_name}</Text>
      </View>
      <Badge label={item.is_active ? 'active' : 'inactive'} variant={item.is_active ? 'success' : 'default'} small />
    </TouchableOpacity>
  );

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-2 border-b border-gray-100">
        <View className="flex-row justify-between items-center mb-3">
          <Text className="text-gray-800 text-xl font-bold">Staff</Text>
          <Text className="text-gray-400 text-sm">{(data ?? []).length} total</Text>
        </View>
        <SearchBar value={search} onChangeText={(t) => { setSearch(t); setPage(1); }} placeholder="Search staff…" />
      </View>
      <FlatList
        data={data ?? []}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
        ListEmptyComponent={() => (
          <View className="items-center mt-16">
            <Ionicons name="person-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No staff found</Text>
          </View>
        )}
        onEndReached={() => { /* staff returns array, no pagination */ }}
        onEndReachedThreshold={0.3}
      />
    </SafeAreaView>
  );
}
