import React from 'react';
import { View, Text, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { dashboardService } from '@/services/dashboard.service';
import { useAuthStore } from '@/stores/authStore';
import { usePermissions } from '@/hooks/usePermissions';
import { StatCard } from '@/components/StatCard';
import { Loading } from '@/components/Loading';
import { COLORS, STALE_5MIN } from '@/constants';

export default function DashboardScreen() {
  const { user, schoolName } = useAuthStore();
  const { isAdmin, isTeacher, isParent, isStudent } = usePermissions();

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey:  ['dashboard'],
    queryFn:   dashboardService.getStats,
    staleTime: STALE_5MIN,
  });

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <ScrollView
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={COLORS.primary} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View className="bg-primary-800 pt-4 pb-8 px-5">
          <View className="flex-row justify-between items-center">
            <View>
              <Text className="text-blue-200 text-sm">{greeting()},</Text>
              <Text className="text-white text-xl font-bold">{user?.full_name ?? user?.username ?? 'User'}</Text>
              <Text className="text-blue-300 text-xs capitalize">{user?.is_super_admin ? 'Super Admin' : 'Admin'} · {schoolName}</Text>
            </View>
            <TouchableOpacity onPress={() => router.push('/(app)/notifications/index')} className="relative">
              <Ionicons name="notifications-outline" size={24} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>

        <View className="px-3 -mt-4">
          {isLoading ? (
            <Loading />
          ) : (
            <>
              {/* KPI Cards */}
              {(isAdmin) && (
                <>
                  <View className="flex-row mt-2">
                    <StatCard
                      label="Students"
                      value={data?.total_students ?? '—'}
                      color={COLORS.primary}
                      icon={<Ionicons name="people" size={18} color={COLORS.primary} />}
                    />
                    <StatCard
                      label="Staff"
                      value={data?.total_staff ?? '—'}
                      color={COLORS.info}
                      icon={<Ionicons name="person" size={18} color={COLORS.info} />}
                    />
                  </View>
                  <View className="flex-row mt-0">
                    <StatCard
                      label="Attendance"
                      value={data?.today_attendance_percent != null ? `${data.today_attendance_percent}%` : '—'}
                      color={COLORS.success}
                      icon={<Ionicons name="checkbox" size={18} color={COLORS.success} />}
                      subtitle="Today"
                    />
                    <StatCard
                      label="Pending Fees"
                      value={data?.pending_fees != null ? `₹${((data.pending_fees) / 1000).toFixed(0)}K` : '—'}
                      color={COLORS.warning}
                      icon={<Ionicons name="wallet" size={18} color={COLORS.warning} />}
                    />
                  </View>
                  {data?.pending_leaves != null && (
                    <View className="flex-row mt-0">
                      <StatCard
                        label="Leave Requests"
                        value={data?.pending_leaves ?? 0}
                        color={COLORS.danger}
                        icon={<Ionicons name="time" size={18} color={COLORS.danger} />}
                        subtitle="Pending approval"
                      />
                      <StatCard
                        label="Fee Collection"
                        value={data?.fee_collection_this_month != null ? `₹${(data.fee_collection_this_month / 1000).toFixed(0)}K` : '—'}
                        color="#8b5cf6"
                        icon={<Ionicons name="trending-up" size={18} color="#8b5cf6" />}
                        subtitle="This month"
                      />
                    </View>
                  )}
                </>
              )}

              {(isTeacher) && (
                <View className="flex-row mt-2">
                  <StatCard label="Attendance" value={data?.today_attendance_percent != null ? `${data.today_attendance_percent}%` : '—'} color={COLORS.success} />
                  <StatCard label="Pending Leaves" value={data?.pending_leaves ?? '—'} color={COLORS.warning} />
                </View>
              )}

              {/* Quick Actions */}
              <View className="bg-white rounded-2xl mt-3 p-4 shadow-sm">
                <Text className="text-gray-700 font-semibold mb-3">Quick Actions</Text>
                <View className="flex-row flex-wrap">
                  {isAdmin && (
                    <>
                      <QuickAction icon="people" label="Students" onPress={() => router.push('/(app)/students/index')} />
                      <QuickAction icon="person-add" label="Admissions" onPress={() => {}} />
                      <QuickAction icon="wallet" label="Fees" onPress={() => router.push('/(app)/fees/index')} />
                      <QuickAction icon="document-text" label="Reports" onPress={() => router.push('/(app)/reports/index')} />
                    </>
                  )}
                  {isTeacher && (
                    <>
                      <QuickAction icon="checkbox" label="Attendance" onPress={() => router.push('/(app)/attendance/index')} />
                      <QuickAction icon="document-text" label="Homework" onPress={() => router.push('/(app)/homework/index')} />
                      <QuickAction icon="calendar" label="Timetable" onPress={() => router.push('/(app)/timetable/index')} />
                      <QuickAction icon="time" label="Leaves" onPress={() => router.push('/(app)/leaves/index')} />
                    </>
                  )}
                  {(isParent || isStudent) && (
                    <>
                      <QuickAction icon="wallet" label="Fees" onPress={() => router.push('/(app)/fees/index')} />
                      <QuickAction icon="calendar" label="Timetable" onPress={() => router.push('/(app)/timetable/index')} />
                      <QuickAction icon="document-text" label="Homework" onPress={() => router.push('/(app)/homework/index')} />
                      <QuickAction icon="trophy" label="Exams" onPress={() => router.push('/(app)/exams/index')} />
                    </>
                  )}
                </View>
              </View>

              {/* Recent Announcements */}
              {(data?.recent_announcements?.length ?? 0) > 0 && (
                <View className="bg-white rounded-2xl mt-3 p-4 shadow-sm mb-4">
                  <View className="flex-row justify-between items-center mb-3">
                    <Text className="text-gray-700 font-semibold">Recent Notices</Text>
                    <TouchableOpacity onPress={() => router.push('/(app)/announcements/index')}>
                      <Text className="text-primary-600 text-xs">View all</Text>
                    </TouchableOpacity>
                  </View>
                  {(data?.recent_announcements ?? []).slice(0, 3).map((a) => (
                    <View key={a.id} className="border-b border-gray-100 pb-2 mb-2">
                      <Text className="text-gray-700 text-sm font-medium" numberOfLines={1}>{a.title}</Text>
                      <Text className="text-gray-400 text-xs mt-0.5">{a.created_by_name}</Text>
                    </View>
                  ))}
                </View>
              )}
            </>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function QuickAction({ icon, label, onPress }: { icon: keyof typeof Ionicons.glyphMap; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} className="w-1/4 items-center mb-4">
      <View className="w-12 h-12 rounded-2xl bg-primary-50 items-center justify-center mb-1">
        <Ionicons name={icon} size={22} color={COLORS.primary} />
      </View>
      <Text className="text-gray-600 text-xs text-center" numberOfLines={1}>{label}</Text>
    </TouchableOpacity>
  );
}
