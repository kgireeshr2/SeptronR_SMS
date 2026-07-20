import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl, Modal, TextInput, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import Toast from 'react-native-toast-message';
import { leavesService } from '@/services/leaves.service';
import { usePermissions } from '@/hooks/usePermissions';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge, leaveStatusBadge } from '@/components/Badge';
import { LeaveApplication } from '@/types';
import { COLORS, STALE_5MIN } from '@/constants';

export default function LeavesScreen() {
  const { isAdmin } = usePermissions();
  const qc = useQueryClient();
  const [showApply, setShowApply] = useState(false);
  const [leaveType, setLeaveType] = useState('');
  const [startDate, setStartDate] = useState(dayjs().format('YYYY-MM-DD'));
  const [endDate,   setEndDate]   = useState(dayjs().format('YYYY-MM-DD'));
  const [reason,    setReason]    = useState('');
  const [tab,       setTab]       = useState<'my' | 'pending'>('my');

  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey:  ['leaves', tab],
    queryFn:   () => tab === 'my' ? leavesService.getMyLeaves() : leavesService.list({ status: 'pending' }),
    staleTime: STALE_5MIN,
  });

  const applyMutation = useMutation({
    mutationFn: () => leavesService.apply({ leave_type: leaveType, start_date: startDate, end_date: endDate, reason }),
    onSuccess:  () => { Toast.show({ type: 'success', text1: 'Leave application submitted!' }); qc.invalidateQueries({ queryKey: ['leaves'] }); setShowApply(false); },
    onError:    () => Toast.show({ type: 'error', text1: 'Failed to submit leave' }),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => leavesService.approve(id),
    onSuccess:  () => { Toast.show({ type: 'success', text1: 'Leave approved' }); qc.invalidateQueries({ queryKey: ['leaves'] }); },
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => leavesService.reject(id),
    onSuccess:  () => { Toast.show({ type: 'success', text1: 'Leave rejected' }); qc.invalidateQueries({ queryKey: ['leaves'] }); },
  });

  const renderItem = ({ item }: { item: LeaveApplication }) => (
    <View className="bg-white mx-4 mb-2 rounded-xl p-4 shadow-sm">
      <View className="flex-row justify-between items-start mb-2">
        <View className="flex-1">
          <Text className="text-gray-800 font-semibold">{item.staff_name ?? 'My Leave'}</Text>
          <Text className="text-gray-400 text-xs">{item.leave_type}</Text>
        </View>
        <Badge label={item.status} variant={leaveStatusBadge(item.status)} small />
      </View>
      <Text className="text-gray-500 text-sm mb-1">{item.reason}</Text>
      <Text className="text-gray-400 text-xs">{item.start_date ? dayjs(item.start_date).format('DD MMM') : ''} – {item.end_date ? dayjs(item.end_date).format('DD MMM YYYY') : ''}</Text>
      {isAdmin && item.status === 'pending' && (
        <View className="flex-row mt-3 space-x-2">
          <TouchableOpacity onPress={() => approveMutation.mutate(item.id)} className="flex-1 bg-green-100 rounded-lg py-2 items-center">
            <Text className="text-green-700 font-medium text-sm">Approve</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => rejectMutation.mutate(item.id)} className="flex-1 bg-red-100 rounded-lg py-2 items-center">
            <Text className="text-red-700 font-medium text-sm">Reject</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  if (isLoading) return <Loading fullScreen />;
  if (isError)   return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100 flex-row justify-between items-center">
        <Text className="text-gray-800 text-xl font-bold">Leaves</Text>
        <TouchableOpacity onPress={() => setShowApply(true)} className="bg-primary-700 rounded-full p-2">
          <Ionicons name="add" size={20} color="#fff" />
        </TouchableOpacity>
      </View>

      {isAdmin && (
        <View className="flex-row bg-white border-b border-gray-100">
          {(['my', 'pending'] as const).map((t) => (
            <TouchableOpacity key={t} onPress={() => setTab(t)} className={`flex-1 py-2.5 items-center ${tab === t ? 'border-b-2 border-primary-600' : ''}`}>
              <Text className={`text-sm font-medium capitalize ${tab === t ? 'text-primary-700' : 'text-gray-400'}`}>{t === 'my' ? 'My Leaves' : 'Pending Approvals'}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <FlatList
        data={Array.isArray(data) ? data : (data?.items ?? [])}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        contentContainerStyle={{ paddingTop: 8, paddingBottom: 24 }}
        ListEmptyComponent={() => (
          <View className="items-center mt-16">
            <Ionicons name="time-outline" size={48} color={COLORS.gray200} />
            <Text className="text-gray-400 mt-2">No leave applications</Text>
          </View>
        )}
      />

      {/* Apply Modal */}
      <Modal visible={showApply} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView className="flex-1 bg-white">
          <View className="px-4 pt-4 pb-3 border-b border-gray-100 flex-row justify-between items-center">
            <Text className="text-gray-800 text-lg font-bold">Apply for Leave</Text>
            <TouchableOpacity onPress={() => setShowApply(false)}><Ionicons name="close" size={24} color={COLORS.gray700} /></TouchableOpacity>
          </View>
          <View className="p-4">
            <Text className="text-gray-600 text-sm font-medium mb-1">Leave Type</Text>
            <TextInput className="border border-gray-200 rounded-xl px-4 py-3 mb-3 text-sm text-gray-700" value={leaveType} onChangeText={setLeaveType} placeholder="Sick / Casual / Annual" />
            <Text className="text-gray-600 text-sm font-medium mb-1">Start Date (YYYY-MM-DD)</Text>
            <TextInput className="border border-gray-200 rounded-xl px-4 py-3 mb-3 text-sm text-gray-700" value={startDate} onChangeText={setStartDate} />
            <Text className="text-gray-600 text-sm font-medium mb-1">End Date (YYYY-MM-DD)</Text>
            <TextInput className="border border-gray-200 rounded-xl px-4 py-3 mb-3 text-sm text-gray-700" value={endDate} onChangeText={setEndDate} />
            <Text className="text-gray-600 text-sm font-medium mb-1">Reason</Text>
            <TextInput className="border border-gray-200 rounded-xl px-4 py-3 mb-6 text-sm text-gray-700" value={reason} onChangeText={setReason} multiline numberOfLines={3} textAlignVertical="top" />
            <TouchableOpacity
              onPress={() => applyMutation.mutate()} disabled={applyMutation.isPending || !leaveType || !reason}
              className={`rounded-xl py-4 items-center ${applyMutation.isPending ? 'bg-primary-300' : 'bg-primary-700'}`}
            >
              <Text className="text-white font-semibold">{applyMutation.isPending ? 'Submitting…' : 'Submit Application'}</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}
