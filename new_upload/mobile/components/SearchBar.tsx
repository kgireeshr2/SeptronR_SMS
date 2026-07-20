import React from 'react';
import { View, TextInput, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '@/constants';

interface SearchBarProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  onClear?: () => void;
}

export function SearchBar({ value, onChangeText, placeholder = 'Search…', onClear }: SearchBarProps) {
  return (
    <View className="flex-row items-center bg-gray-100 rounded-xl px-3 py-2 mx-4 mb-3">
      <Ionicons name="search-outline" size={18} color={COLORS.gray500} />
      <TextInput
        className="flex-1 ml-2 text-sm text-gray-700"
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={COLORS.gray500}
        returnKeyType="search"
        autoCorrect={false}
      />
      {value.length > 0 && (
        <TouchableOpacity onPress={() => { onChangeText(''); onClear?.(); }}>
          <Ionicons name="close-circle" size={18} color={COLORS.gray500} />
        </TouchableOpacity>
      )}
    </View>
  );
}
