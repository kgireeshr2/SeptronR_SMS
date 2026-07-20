import React from 'react';
import { View, ActivityIndicator, Text } from 'react-native';
import { COLORS } from '@/constants';

interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
}

export function Loading({ message = 'Loading…', fullScreen = false }: LoadingProps) {
  if (fullScreen) {
    return (
      <View className="flex-1 items-center justify-center bg-white">
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text className="mt-3 text-gray-500 text-sm">{message}</Text>
      </View>
    );
  }
  return (
    <View className="py-8 items-center justify-center">
      <ActivityIndicator size="small" color={COLORS.primary} />
      {message ? <Text className="mt-2 text-gray-400 text-xs">{message}</Text> : null}
    </View>
  );
}
