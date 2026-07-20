import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '@/constants';

export default function NotFoundScreen() {
  return (
    <SafeAreaView className="flex-1 bg-white items-center justify-center p-6">
      <Ionicons name="alert-circle-outline" size={72} color={COLORS.gray200} />
      <Text className="text-gray-700 text-2xl font-bold mt-4">Page Not Found</Text>
      <Text className="text-gray-400 text-sm mt-2 text-center">The screen you're looking for doesn't exist.</Text>
      <TouchableOpacity onPress={() => router.replace('/(app)/dashboard')} className="mt-8 px-8 py-3 bg-primary-700 rounded-xl">
        <Text className="text-white font-semibold">Go Home</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}
