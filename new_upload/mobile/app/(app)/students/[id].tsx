import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { studentsService } from '@/services/students.service';
import { Loading } from '@/components/Loading';
import { ErrorView } from '@/components/ErrorView';
import { Badge } from '@/components/Badge';
import { COLORS } from '@/constants';

export default function StudentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const studentId = id as string;

  const { data: student, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['student', studentId],
    queryFn:  () => studentsService.get(studentId),
    enabled:  !!studentId,
  });

  if (isLoading) return <Loading fullScreen />;
  if (isError || !student) return <ErrorView onRetry={refetch} />;

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <ScrollView
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
      >
        {/* Back + header */}
        <View className="bg-primary-800 pt-4 pb-8 px-4">
          <TouchableOpacity onPress={() => router.back()} className="mb-4">
            <Ionicons name="arrow-back" size={22} color="#fff" />
          </TouchableOpacity>
          <View className="items-center">
            <View className="w-20 h-20 rounded-full bg-primary-200 items-center justify-center mb-2">
              <Text className="text-primary-800 text-3xl font-bold">
                {(student.full_name ?? '').charAt(0)}
              </Text>
            </View>
            <Text className="text-white text-xl font-bold">{student.full_name}</Text>
            <Text className="text-blue-200 text-sm">{student.admission_number}</Text>
            <Badge label={student.status ?? 'active'} variant={student.status === 'active' ? 'success' : 'default'} />
          </View>
        </View>

        {/* Info Cards */}
        <View className="bg-white rounded-2xl mx-4 -mt-4 p-4 shadow-sm">
          <Text className="text-gray-700 font-semibold mb-3">Academic Info</Text>
          <InfoRow label="Class"   value={`${student.class_name ?? ''} - ${student.section_name ?? ''}`} />
          <InfoRow label="Gender"  value={student.gender ?? ''} />
          <InfoRow label="DOB"     value={student.date_of_birth ? new Date(student.date_of_birth).toLocaleDateString() : ''} />
        </View>

        <View className="bg-white rounded-2xl mx-4 mt-3 p-4 shadow-sm">
          <Text className="text-gray-700 font-semibold mb-3">Parent / Guardian</Text>
          <InfoRow label="Name"  value={student.parent_name ?? ''} />
          <InfoRow label="Phone" value={student.parent_phone ?? ''} />
        </View>

        {/* Quick links */}
        <View className="bg-white rounded-2xl mx-4 mt-3 p-4 shadow-sm mb-6">
          <Text className="text-gray-700 font-semibold mb-3">Quick Links</Text>
          <View className="flex-row flex-wrap">
            <LinkChip icon="calendar" label="Attendance" onPress={() => {}} />
            <LinkChip icon="wallet"   label="Fees"       onPress={() => router.push('/(app)/fees/index')} />
            <LinkChip icon="trophy"   label="Results"    onPress={() => router.push('/(app)/exams/index')} />
            <LinkChip icon="bus"      label="Transport"  onPress={() => router.push('/(app)/transport/index')} />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row justify-between py-2 border-b border-gray-50">
      <Text className="text-gray-400 text-sm">{label}</Text>
      <Text className="text-gray-700 text-sm font-medium">{value}</Text>
    </View>
  );
}

function LinkChip({ icon, label, onPress }: { icon: keyof typeof Ionicons.glyphMap; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} className="mr-2 mb-2 flex-row items-center bg-gray-100 rounded-full px-3 py-1.5">
      <Ionicons name={icon} size={14} color={COLORS.primary} />
      <Text className="text-gray-700 text-xs ml-1">{label}</Text>
    </TouchableOpacity>
  );
}
