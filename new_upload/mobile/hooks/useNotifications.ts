import { useEffect, useRef } from 'react';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { router } from 'expo-router';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/stores/authStore';

// Configure how notifications appear while app is in the foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert:   true,
    shouldPlaySound:   true,
    shouldSetBadge:    true,
  }),
});

export function useNotifications() {
  const notificationListener    = useRef<Notifications.EventSubscription>();
  const responseListener        = useRef<Notifications.EventSubscription>();
  const { isAuthenticated }     = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) return;

    registerForPushNotifications();

    // Foreground notification received
    notificationListener.current = Notifications.addNotificationReceivedListener((notification) => {
      console.log('[Notification received]', notification);
    });

    // User tapped a notification
    responseListener.current = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as Record<string, string>;
      handleNotificationNavigation(data);
    });

    return () => {
      notificationListener.current?.remove();
      responseListener.current?.remove();
    };
  }, [isAuthenticated]);
}

async function registerForPushNotifications() {
  if (!Device.isDevice) return; // Skip in emulator for Expo Go

  // Android channel
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name:       'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#1e40af',
    });
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.warn('Push notification permission not granted');
    return;
  }

  try {
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    await authService.registerFcmToken(token);
    console.log('[FCM token registered]', token);
  } catch (err) {
    console.error('[FCM token registration failed]', err);
  }
}

function handleNotificationNavigation(data: Record<string, string>) {
  const { type, id } = data;
  switch (type) {
    case 'fee':         router.push(`/(app)/fees/${id}`);         break;
    case 'homework':    router.push(`/(app)/homework/${id}`);     break;
    case 'exam':        router.push(`/(app)/exams/${id}`);        break;
    case 'leave':       router.push(`/(app)/leaves/${id}`);       break;
    case 'announcement':router.push(`/(app)/announcements/${id}`); break;
    default:            router.push('/(app)/notifications');      break;
  }
}
