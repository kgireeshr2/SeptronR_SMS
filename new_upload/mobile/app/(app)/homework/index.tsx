import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl, Modal, TextInput, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import Toast from 'react-native-toast-message';
import { homeworkService } from '@/services/homework.service';
import { usePermissions } from '@/hooks/usePermissions';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Homework } from '@/types';
import { COLORS, STALE_5MIN } from '@/constants';

export default function HomeworkScreen() {
  const { isTeacher, isAdmin } = usePermissions();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [title,   setTitle]   = useState('');
  const [desc,    setDesc]    = useState('');
  const [dueDate, setDueDate] = useState(dayjs().add(1, 'day').format('YYYY-MM-DD'));

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['homework'],
    queryFn:   () => homeworkService.list({}),
    staleTime: STALE_5MIN,
  });

  const mutation = useMutation({
    mutationFn: () => homeworkService.create({
      title, description: desc, due_date: dueDate,
    }),
    onSuccess: () => {
      Toast.show({ type: 'success', text1: 'Homework created!' });
      qc.invalidateQueries({ queryKey: ['homework'] });
      setShowCreate(false); setTitle(''); setDesc('');
    },
    onError: () => Toast.show({ type: 'error', text1: 'Failed to create homework' }),
  });

  const renderItem = ({ item }: { item: Homework }) => (
    <View className="bg-white mx-4 mb-2 rounded-xl p-4 shadow-sm">
      <View className="flex-row justify-between items-start">
        <View className="flex-1">
          <Text className="text-gray-800 font-semibold">{item.title}</Text>
          <Text className="text-gray-500 text-sm mt-1" numberOfLines={2}>{item.description}</Text>
        </View>
      </View>
      <View className="flex-row mt-3 justify-between">
        <Text className="text-gray-400 text-xs">{item.subject_name} · {item.class_name}</Text>
        <View className="flex-row items-center">
          <Ionicons name="calendar-outline" size={12} color={item.due_date && dayjs(item.due_date).isBefore(dayjs()) ? COLORS.danger : COLORS.gray500} />
          <Text style={{ color: item.due_date && dayjs(item.due_date).isBefore(dayjs()) ? COLORS.danger : COLORS.gray500 }} className="text-xs ml-1">
            Due {item.due_date ? dayjs(item.due_date).format('DD MMM') : 'TBD'}
          </Text>
        </View>
      </View>
    </View>
  );

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100 flex-row justify-between items-center">
        <Text className="text-gray-800 text-xl font-bold">Homework</Text>
        {(isTeacher || isAdmin) && (
          <TouchableOpacity onPress={() => setShowCreate(true)} className="bg-primary-700 rounded-full p-2">
            <Ionicons name="add" size={20} color="#fff" />
          </TouchableOpacity>
        )}
      </View>
      <FlatList
        data={Array.isArray(data) ? data : (data?.items ?? [])}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
        ListEmptyComponent={() => (
          <View className="items-center mt-16">
            <Ionicons name="document-text-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No homework assigned</Text>
          </View>
        )}
      />

      {/* Create Modal */}
      <Modal visible={showCreate} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView className="flex-1 bg-white">
          <View className="px-4 pt-4 pb-3 border-b border-gray-100 flex-row justify-between items-center">
            <Text className="text-gray-800 text-lg font-bold">New Homework</Text>
            <TouchableOpacity onPress={() => setShowCreate(false)}>
              <Ionicons name="close" size={24} color={COLORS.gray700} />
            </TouchableOpacity>
          </View>
          <View className="p-4">
            <Text className="text-gray-600 text-sm font-medium mb-1">Title</Text>
            <TextInput className="border border-gray-200 rounded-xl px-4 py-3 mb-4 text-sm text-gray-700" value={title} onChangeText={setTitle} placeholder="Homework title" />
            <Text className="text-gray-600 text-sm font-medium mb-1">Description</Text>
            <TextInput
              className="border border-gray-200 rounded-xl px-4 py-3 mb-4 text-sm text-gray-700"
              value={desc} onChangeText={setDesc} placeholder="Describe the homework…"
              multiline numberOfLines={4} textAlignVertical="top"
            />
            <Text className="text-gray-600 text-sm font-medium mb-1">Due Date (YYYY-MM-DD)</Text>
            <TextInput className="border border-gray-200 rounded-xl px-4 py-3 mb-6 text-sm text-gray-700" value={dueDate} onChangeText={setDueDate} />
            <TouchableOpacity
              onPress={() => mutation.mutate()} disabled={mutation.isPending || !title}
              className={`rounded-xl py-4 items-center ${mutation.isPending || !title ? 'bg-primary-300' : 'bg-primary-700'}`}
            >
              <Text className="text-white font-semibold">{mutation.isPending ? 'Saving…' : 'Create Homework'}</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}
