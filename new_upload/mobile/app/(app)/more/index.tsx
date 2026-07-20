import React from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { usePermissions } from '@/hooks/usePermissions';
import { COLORS } from '@/constants';

type MenuItem = {
  icon:  keyof typeof Ionicons.glyphMap;
  label: string;
  route: string;
  color: string;
  roles?: string[];
};

const MENU_ITEMS: MenuItem[] = [
  { icon: 'bus-outline',           label: 'Transport',      route: '/(app)/transport/index',     color: '#f59e0b'  },
  { icon: 'book-outline',          label: 'Library',        route: '/(app)/library/index',       color: '#8b5cf6'  },
  { icon: 'calendar-outline',      label: 'Calendar',       route: '/(app)/calendar/index',      color: '#06b6d4'  },
  { icon: 'megaphone-outline',     label: 'Announcements',  route: '/(app)/announcements/index', color: '#f97316'  },
  { icon: 'bar-chart-outline',     label: 'Reports',        route: '/(app)/reports/index',       color: '#6366f1', roles: ['admin', 'super_admin'] },
  { icon: 'people-outline',        label: 'Students',       route: '/(app)/students/index',      color: '#14b8a6', roles: ['admin', 'super_admin', 'teacher'] },
  { icon: 'person-outline',        label: 'Staff',          route: '/(app)/staff/index',         color: '#3b82f6', roles: ['admin', 'super_admin'] },
  { icon: 'checkmark-circle-outline', label: 'Attendance',  route: '/(app)/attendance/index',    color: '#22c55e'  },
  { icon: 'trophy-outline',        label: 'Exams',          route: '/(app)/exams/index',         color: '#eab308'  },
  { icon: 'time-outline',          label: 'Leaves',         route: '/(app)/leaves/index',        color: '#ef4444', roles: ['admin', 'super_admin', 'staff', 'teacher'] },
  { icon: 'notifications-outline', label: 'Notifications',  route: '/(app)/notifications/index', color: '#ec4899'  },
  { icon: 'settings-outline',      label: 'Settings',       route: '/(app)/settings/index',      color: '#6b7280'  },
];

export default function MoreScreen() {
  const { isAdmin, isSuperAdmin, isTeacher, isStaff, role } = usePermissions();

  const visibleItems = MENU_ITEMS.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(role ?? '');
  });

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="bg-white px-4 pt-4 pb-3 border-b border-gray-100">
        <Text className="text-gray-800 text-xl font-bold">More</Text>
      </View>
      <ScrollView contentContainerStyle={{ padding: 16 }}>
        <View className="flex-row flex-wrap">
          {visibleItems.map((item) => (
            <TouchableOpacity
              key={item.label}
              onPress={() => router.push(item.route as any)}
              className="w-1/3 items-center mb-6 px-2"
            >
              <View
                className="w-14 h-14 rounded-2xl items-center justify-center mb-2 shadow-sm"
                style={{ backgroundColor: `${item.color}18` }}
              >
                <Ionicons name={item.icon} size={26} color={item.color} />
              </View>
              <Text className="text-gray-600 text-xs text-center font-medium" numberOfLines={1}>{item.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
