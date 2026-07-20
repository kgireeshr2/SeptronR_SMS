import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import { libraryService } from '@/services/misc.service';
import { SearchBar } from '@/components/SearchBar';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge } from '@/components/Badge';
import { COLORS, STALE_5MIN } from '@/constants';

export default function LibraryScreen() {
  const [search, setSearch] = useState('');
  const [tab, setTab]       = useState<'books' | 'issued'>('books');

  const { data: books, isLoading: bLoading, isError: bError, refetch: bRefetch, isRefetching: bRefetching } = useQuery({
    queryKey:  ['library-books', search],
    queryFn:   () => libraryService.searchBooks(search),
    staleTime: STALE_5MIN,
    enabled:   tab === 'books',
  });

  const { data: issued, isLoading: iLoading, isError: iError, refetch: iRefetch, isRefetching: iRefetching } = useQuery({
    queryKey:  ['issued-books'],
    queryFn:   libraryService.getMyIssuedBooks,
    staleTime: STALE_5MIN,
    enabled:   tab === 'issued',
  });

  const isLoading   = tab === 'books' ? bLoading   : iLoading;
  const isError     = tab === 'books' ? bError     : iError;
  const refetch     = tab === 'books' ? bRefetch   : iRefetch;
  const isRefetching = tab === 'books' ? bRefetching : iRefetching;
  const listData    = (tab === 'books' ? (books as any)?.items ?? books ?? [] : issued ?? []) as any[];

  if (isLoading) return <Loading fullScreen />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-0 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold mb-3">Library</Text>
        <View className="flex-row">
          {(['books', 'issued'] as const).map((t) => (
            <TouchableOpacity key={t} onPress={() => setTab(t)} className={`flex-1 py-2.5 items-center ${tab === t ? 'border-b-2 border-primary-600' : ''}`}>
              <Text className={`text-sm font-medium capitalize ${tab === t ? 'text-primary-700' : 'text-gray-400'}`}>{t === 'books' ? 'All Books' : 'Issued to Me'}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
      {tab === 'books' && (
        <View className="pt-3">
          <SearchBar value={search} onChangeText={setSearch} placeholder="Search books…" />
        </View>
      )}
      {isError ? (
        <ErrorView onRetry={refetch} />
      ) : (
        <FlatList
          data={listData}
          keyExtractor={(i: any) => String(i.id)}
          refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch as any} tintColor={COLORS.primary} />}
          renderItem={({ item }: { item: any }) => (
            <View className="bg-white mx-4 mb-2 rounded-xl p-4 flex-row shadow-sm">
              <View className="w-10 h-10 rounded-lg bg-indigo-100 items-center justify-center mr-3">
                <Ionicons name="book" size={20} color="#4f46e5" />
              </View>
              <View className="flex-1">
                <Text className="text-gray-800 font-semibold text-sm">{item.title}</Text>
                <Text className="text-gray-400 text-xs">{item.author ?? item.authorName}</Text>
                {tab === 'issued' && (
                  <Text className={`text-xs mt-1 ${dayjs(item.dueDate).isBefore(dayjs()) ? 'text-red-500' : 'text-gray-400'}`}>
                    Due: {item.dueDate ? dayjs(item.dueDate).format('DD MMM YYYY') : '—'}
                  </Text>
                )}
              </View>
              {tab === 'books' && (
                <Badge label={item.status ?? (item.availableCopies > 0 ? 'Available' : 'Unavailable')} variant={item.availableCopies > 0 ? 'success' : 'danger'} small />
              )}
            </View>
          )}
          contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
          ListEmptyComponent={() => (
            <View className="items-center mt-16">
              <Ionicons name="book-outline" size={48} color={COLORS.gray200} />
              <Text className="text-gray-400 mt-2">{tab === 'books' ? 'No books found' : 'No books issued'}</Text>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}
