import React from 'react';
import { View, Text } from 'react-native';

interface StatCardProps {
  label: string;
  value: string | number;
  color?: string;
  icon?: React.ReactNode;
  subtitle?: string;
}

export function StatCard({ label, value, color = '#1e40af', icon, subtitle }: StatCardProps) {
  return (
    <View
      className="flex-1 m-1 rounded-xl p-4 bg-white shadow-sm"
      style={{ borderLeftWidth: 4, borderLeftColor: color }}
    >
      <View className="flex-row items-center justify-between">
        <Text className="text-gray-500 text-xs font-medium uppercase tracking-wide">{label}</Text>
        {icon}
      </View>
      <Text className="mt-2 text-2xl font-bold text-gray-800">{value}</Text>
      {subtitle ? <Text className="mt-1 text-xs text-gray-400">{subtitle}</Text> : null}
    </View>
  );
}
