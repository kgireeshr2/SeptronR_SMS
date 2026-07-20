import React, { useEffect } from 'react';
import { Tabs, router } from 'expo-router';
import { View, TouchableOpacity, Text, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/stores/authStore';
import { useAcademicYearStore } from '@/stores/academicYearStore';
import { usePermissions } from '@/hooks/usePermissions';
import { COLORS } from '@/constants';

type TabConfig = {
  name:  string;
  title: string;
  icon:  keyof typeof Ionicons.glyphMap;
};

const ADMIN_TABS: TabConfig[] = [
  { name: 'dashboard/index',   title: 'Dashboard',   icon: 'grid-outline'    },
  { name: 'students/index',    title: 'Students',    icon: 'people-outline'  },
  { name: 'staff/index',       title: 'Staff',       icon: 'person-outline'  },
  { name: 'fees/index',        title: 'Fees',        icon: 'wallet-outline'  },
  { name: 'more/index',        title: 'More',        icon: 'menu-outline'    },
];

const TEACHER_TABS: TabConfig[] = [
  { name: 'dashboard/index',   title: 'Dashboard',  icon: 'grid-outline'        },
  { name: 'attendance/index',  title: 'Attendance', icon: 'checkbox-outline'    },
  { name: 'homework/index',    title: 'Homework',   icon: 'document-text-outline'},
  { name: 'timetable/index',   title: 'Timetable',  icon: 'calendar-outline'    },
  { name: 'more/index',        title: 'More',       icon: 'menu-outline'        },
];

const PARENT_TABS: TabConfig[] = [
  { name: 'dashboard/index',      title: 'Home',         icon: 'home-outline'         },
  { name: 'fees/index',           title: 'Fees',         icon: 'wallet-outline'       },
  { name: 'attendance/index',     title: 'Attendance',   icon: 'checkbox-outline'     },
  { name: 'announcements/index',  title: 'Notices',      icon: 'megaphone-outline'    },
  { name: 'more/index',           title: 'More',         icon: 'menu-outline'         },
];

const STUDENT_TABS: TabConfig[] = [
  { name: 'dashboard/index',      title: 'Home',         icon: 'home-outline'         },
  { name: 'timetable/index',      title: 'Timetable',    icon: 'calendar-outline'     },
  { name: 'homework/index',       title: 'Homework',     icon: 'document-text-outline'},
  { name: 'exams/index',          title: 'Exams',        icon: 'trophy-outline'       },
  { name: 'more/index',           title: 'More',         icon: 'menu-outline'         },
];

function getTabsForRole(role: string | null): TabConfig[] {
  switch (role) {
    case 'super_admin':
    case 'admin':    return ADMIN_TABS;
    case 'teacher':
    case 'staff':    return TEACHER_TABS;
    case 'parent':   return PARENT_TABS;
    case 'student':  return STUDENT_TABS;
    default:         return ADMIN_TABS;
  }
}

// All possible screen names (needed so Expo Router doesn't hide them)
const ALL_SCREENS = [
  'dashboard/index', 'students/index', 'students/[id]',
  'staff/index', 'staff/[id]',
  'attendance/index', 'fees/index', 'fees/[id]',
  'exams/index', 'homework/index', 'timetable/index',
  'leaves/index', 'announcements/index', 'transport/index',
  'library/index', 'calendar/index', 'settings/index',
  'notifications/index', 'reports/index', 'more/index',
];

export default function AppLayout() {
  const { isAuthenticated } = useAuthStore();
  const { fetchYears } = useAcademicYearStore();
  // Use permission-based role inference (matches usePermissions hook logic)
  const { role } = usePermissions();
  const tabs = getTabsForRole(role);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/(auth)/login');
    } else {
      fetchYears();
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  // Build a set of tab names for quick lookup
  const tabNames = new Set(tabs.map((t) => t.name));

  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth:  1,
          borderTopColor:  '#e5e7eb',
          paddingBottom:   Platform.OS === 'ios' ? 20 : 8,
          height:          Platform.OS === 'ios' ? 80 : 64,
        },
        tabBarActiveTintColor:   COLORS.primary,
        tabBarInactiveTintColor: COLORS.gray500,
        tabBarLabelStyle: { fontSize: 10, fontWeight: '600' },
        tabBarIcon: ({ focused, color, size }) => {
          const tab = tabs.find((t) => t.name === route.name);
          const iconName = tab?.icon ?? 'grid-outline';
          return <Ionicons name={focused ? iconName.replace('-outline', '') as any : iconName} size={22} color={color} />;
        },
        tabBarButton: tabNames.has(route.name) ? undefined : () => null,
      })}
    >
      {ALL_SCREENS.map((screen) => (
        <Tabs.Screen
          key={screen}
          name={screen}
          options={{
            title: tabs.find((t) => t.name === screen)?.title ?? screen,
            href:  tabNames.has(screen) ? undefined : null,
          }}
        />
      ))}
    </Tabs>
  );
}
