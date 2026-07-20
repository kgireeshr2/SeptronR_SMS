import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '@/constants';

interface ErrorViewProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorView({ message = 'Something went wrong', onRetry }: ErrorViewProps) {
  return (
    <View className="flex-1 items-center justify-center p-6">
      <Ionicons name="alert-circle-outline" size={48} color={COLORS.danger} />
      <Text className="mt-3 text-gray-700 text-base text-center font-medium">{message}</Text>
      {onRetry && (
        <TouchableOpacity
          onPress={onRetry}
          className="mt-4 px-6 py-2 bg-primary-600 rounded-full"
        >
          <Text className="text-white font-medium">Retry</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}
