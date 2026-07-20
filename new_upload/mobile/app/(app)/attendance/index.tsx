import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, FlatList, RefreshControl, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import dayjs from 'dayjs';
import { attendanceService } from '@/services/attendance.service';
import { useAuthStore } from '@/stores/authStore';
import { usePermissions } from '@/hooks/usePermissions';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge, attendanceBadge } from '@/components/Badge';
import { COLORS } from '@/constants';
import api from '@/services/api';

type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused';

export default function AttendanceScreen() {
  const { isTeacher, isAdmin, isParent, isStudent } = usePermissions();
  const { user } = useAuthStore();
  const qc = useQueryClient();
  const today = dayjs().format('YYYY-MM-DD');

  // For teachers/admin — class picker
  const [selectedDate,    setSelectedDate]    = useState(today);
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);

  // Fetch classes for teacher picker
  const { data: classes } = useQuery({
    queryKey: ['classes-simple'],
    queryFn:  () => api.get('/classes').then((r) => r.data),
    enabled:  isTeacher || isAdmin,
  });

  // Fetch attendance records
  const { data: records, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['attendance', selectedDate, selectedClassId, selectedSection],
    queryFn:  () => attendanceService.getByDate(selectedDate, selectedClassId!, selectedSection!),
    enabled:  (isTeacher || isAdmin) && !!selectedClassId && !!selectedSection,
  });

  // For parent/student — monthly summary
  const monthYear = dayjs();
  const { data: summary } = useQuery({
    queryKey: ['attendance-summary', user?.id, monthYear.month() + 1, monthYear.year()],
    queryFn:  () => attendanceService.getStudentSummary(user!.id, monthYear.month() + 1, monthYear.year()),
    enabled:  isParent || isStudent,
  });

  // Mark attendance
  const [localMarks, setLocalMarks] = useState<Record<string, AttendanceStatus>>({});
  const mutation = useMutation({
    mutationFn: () => {
      const recs = Object.entries(localMarks).map(([sId, status]) => ({ student_id: sId, status }));
      return attendanceService.markBulk(selectedDate, selectedClassId!, selectedSection!, recs);
    },
    onSuccess: () => {
      Toast.show({ type: 'success', text1: 'Attendance saved!' });
      qc.invalidateQueries({ queryKey: ['attendance'] });
    },
    onError: () => Toast.show({ type: 'error', text1: 'Failed to save attendance' }),
  });

  const toggleStatus = (studentId: string, current: string) => {
    const cycle: AttendanceStatus[] = ['present', 'absent', 'late', 'excused'];
    const idx  = cycle.indexOf(current as AttendanceStatus);
    const next = cycle[(idx + 1) % cycle.length];
    setLocalMarks((prev) => ({ ...prev, [studentId]: next }));
  };

  // ─── Parent / Student view ───────────────────────────────────────────────────
  if (isParent || isStudent) {
    return (
      <SafeAreaView className="flex-1 bg-gray-50">
        <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
          <Text className="text-gray-800 text-xl font-bold">Attendance</Text>
          <Text className="text-gray-400 text-sm">{monthYear.format('MMMM YYYY')}</Text>
        </View>
        <ScrollView contentContainerStyle={{ padding: 16 }}>
          {summary ? (
            <View className="bg-white rounded-2xl p-4 shadow-sm">
              <View className="flex-row justify-between mb-4">
                <SummaryPill label="Present"  value={summary.present  ?? 0} color={COLORS.success} />
                <SummaryPill label="Absent"   value={summary.absent   ?? 0} color={COLORS.danger}  />
                <SummaryPill label="Late"     value={summary.late     ?? 0} color={COLORS.warning} />
                <SummaryPill label="Total"    value={summary.total    ?? 0} color={COLORS.primary} />
              </View>
              <View className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <View
                  style={{ width: `${summary.percentage ?? 0}%`, backgroundColor: COLORS.success }}
                  className="h-full rounded-full"
                />
              </View>
              <Text className="text-center text-gray-500 text-sm mt-2">{summary.percentage ?? 0}% Attendance</Text>
            </View>
          ) : (
            <Loading />
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ─── Teacher / Admin view ────────────────────────────────────────────────────
  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">Mark Attendance</Text>
        <Text className="text-gray-400 text-sm">{dayjs(selectedDate).format('ddd, DD MMM YYYY')}</Text>
      </View>

      {/* Class picker placeholder */}
      {!selectedClassId && (
        <View className="flex-1 items-center justify-center">
          <Ionicons name="school-outline" size={48} color={COLORS.gray200} />
          <Text className="text-gray-400 mt-2">Select a class/section to begin</Text>
          {/* TODO: replace with real class picker modal */}
          <TouchableOpacity
            className="mt-4 bg-primary-700 px-6 py-3 rounded-xl"
            onPress={() => Alert.alert('Select Class', 'Implement class picker')}
          >
            <Text className="text-white font-medium">Choose Class</Text>
          </TouchableOpacity>
        </View>
      )}

      {selectedClassId && (
        <>
          {isLoading && <Loading />}
          {isError   && <ErrorView onRetry={refetch} />}
          {records   && (
            <>
              <FlatList
                data={records}
                keyExtractor={(i: any) => String(i.studentId)}
                refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
                renderItem={({ item }: { item: any }) => {
                  const status = localMarks[item.studentId] ?? item.status ?? 'present';
                  return (
                    <TouchableOpacity
                      onPress={() => toggleStatus(item.studentId, status)}
                      className="bg-white mx-4 mb-2 rounded-xl px-4 py-3 flex-row items-center shadow-sm"
                    >
                      <View className="w-10 h-10 rounded-full bg-gray-100 items-center justify-center mr-3">
                        <Text className="text-gray-600 font-bold">{item.studentName?.charAt(0)}</Text>
                      </View>
                      <Text className="flex-1 text-gray-700 font-medium">{item.studentName}</Text>
                      <Badge label={status} variant={attendanceBadge(status)} />
                    </TouchableOpacity>
                  );
                }}
                contentContainerStyle={{ paddingTop: 8, paddingBottom: 100 }}
              />
              <View className="absolute bottom-4 left-4 right-4">
                <TouchableOpacity
                  onPress={() => mutation.mutate()}
                  disabled={mutation.isPending || Object.keys(localMarks).length === 0}
                  className={`rounded-xl py-4 items-center ${mutation.isPending ? 'bg-primary-300' : 'bg-primary-700'}`}
                >
                  <Text className="text-white font-semibold">
                    {mutation.isPending ? 'Saving…' : 'Save Attendance'}
                  </Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </>
      )}
    </SafeAreaView>
  );
}

function SummaryPill({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View className="items-center">
      <Text style={{ color }} className="text-2xl font-bold">{value}</Text>
      <Text className="text-gray-400 text-xs">{label}</Text>
    </View>
  );
}
