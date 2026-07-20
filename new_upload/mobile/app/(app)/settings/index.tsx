import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Switch, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { useAcademicYearStore } from '@/stores/academicYearStore';
import { COLORS } from '@/constants';

export default function SettingsScreen() {
  const { user, logout } = useAuthStore();
  const { allYears, selectedYearId, selectYear } = useAcademicYearStore();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: async () => { await logout(); router.replace('/(auth)/login'); } },
    ]);
  };

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">Settings</Text>
      </View>
      <ScrollView contentContainerStyle={{ padding: 16 }}>
        {/* Profile card */}
        <View className="bg-white rounded-2xl p-4 shadow-sm mb-4">
          <View className="flex-row items-center">
            <View className="w-14 h-14 rounded-full bg-primary-100 items-center justify-center mr-3">
              <Text className="text-primary-700 font-bold text-xl">{(user?.full_name ?? user?.username ?? '?').charAt(0)}</Text>
            </View>
            <View className="flex-1">
              <Text className="text-gray-800 font-bold text-base">{user?.full_name ?? user?.username}</Text>
              <Text className="text-gray-400 text-sm">{user?.email}</Text>
              <Text className="text-primary-600 text-xs capitalize">{user?.is_super_admin ? 'Super Admin' : 'Admin'}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={COLORS.gray500} />
          </View>
        </View>

        {/* Academic Year */}
        <Section title="Academic Year">
          {allYears.map((y) => (
            <TouchableOpacity key={y.id} onPress={() => selectYear(y.id)} className="flex-row items-center justify-between py-3 border-b border-gray-50">
              <View>
                <Text className="text-gray-700 font-medium">{y.name}</Text>
                <Text className="text-gray-400 text-xs">{y.start_date} – {y.end_date}</Text>
              </View>
              {selectedYearId === y.id && <Ionicons name="checkmark-circle" size={20} color={COLORS.success} />}
            </TouchableOpacity>
          ))}
        </Section>

        {/* Notifications */}
        <Section title="Notifications">
          <View className="flex-row items-center justify-between py-3">
            <Text className="text-gray-700">Push Notifications</Text>
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{ false: COLORS.gray200, true: COLORS.primaryLight }}
              thumbColor={notificationsEnabled ? COLORS.primary : '#fff'}
            />
          </View>
        </Section>

        {/* Account */}
        <Section title="Account">
          <SettingsRow icon="lock-closed-outline" label="Change Password" onPress={() => {}} />
          <SettingsRow icon="school-outline"      label="School: {user?.schoolName}" onPress={() => {}} />
        </Section>

        {/* Danger zone */}
        <TouchableOpacity onPress={handleLogout} className="bg-red-50 rounded-2xl p-4 flex-row items-center mt-2">
          <Ionicons name="log-out-outline" size={20} color={COLORS.danger} />
          <Text className="text-red-600 font-semibold ml-2">Sign Out</Text>
        </TouchableOpacity>

        <Text className="text-center text-gray-300 text-xs mt-6">SeptroSchool v1.0.0 · {process.env.EXPO_PUBLIC_APP_ENV}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View className="bg-white rounded-2xl p-4 shadow-sm mb-4">
      <Text className="text-gray-400 text-xs font-semibold uppercase tracking-wide mb-2">{title}</Text>
      {children}
    </View>
  );
}

function SettingsRow({ icon, label, onPress }: { icon: keyof typeof Ionicons.glyphMap; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} className="flex-row items-center py-3 border-b border-gray-50">
      <Ionicons name={icon} size={18} color={COLORS.gray500} />
      <Text className="flex-1 text-gray-700 ml-3">{label}</Text>
      <Ionicons name="chevron-forward" size={16} color={COLORS.gray500} />
    </TouchableOpacity>
  );
}
