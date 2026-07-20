import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, KeyboardAvoidingView,
  Platform, ScrollView, ActivityIndicator, Image,
} from 'react-native';
import { router } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import Toast from 'react-native-toast-message';
import { useAuthStore } from '@/stores/authStore';
import { COLORS } from '@/constants';

const schema = z.object({
  schoolSlug: z.string().min(2, 'School ID is required'),
  username:   z.string().min(2, 'Username is required'),
  password:   z.string().min(4, 'Password is required'),
});

type FormData = z.infer<typeof schema>;

export default function LoginScreen() {
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuthStore();

  const {
    control, handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { schoolSlug: '', username: '', password: '' },
  });

  const onSubmit = async (data: FormData) => {
    try {
      await login(data.username, data.password, data.schoolSlug);
      router.replace('/(app)/dashboard');
    } catch (err: any) {
      const msg = err?.message ?? err?.response?.data?.detail ?? 'Invalid credentials. Please try again.';
      Toast.show({ type: 'error', text1: 'Login Failed', text2: msg });
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-primary-800">
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        className="flex-1"
      >
        <ScrollView contentContainerStyle={{ flexGrow: 1 }} keyboardShouldPersistTaps="handled">
          {/* Header */}
          <View className="items-center pt-16 pb-8">
            <View className="w-20 h-20 rounded-2xl bg-white items-center justify-center shadow-lg mb-4">
              <Ionicons name="school" size={40} color={COLORS.primary} />
            </View>
            <Text className="text-white text-3xl font-bold">SeptroSchool</Text>
            <Text className="text-blue-200 text-sm mt-1">by SeptronR</Text>
          </View>

          {/* Card */}
          <View className="flex-1 bg-white rounded-t-3xl px-6 pt-8 pb-6 shadow-xl">
            <Text className="text-gray-800 text-2xl font-bold mb-1">Welcome back</Text>
            <Text className="text-gray-400 text-sm mb-8">Sign in to your school account</Text>

            {/* School Slug */}
            <Text className="text-gray-600 text-sm font-medium mb-1">School ID</Text>
            <Controller
              control={control}
              name="schoolSlug"
              render={({ field: { onChange, value } }) => (
                <View className={`flex-row items-center border rounded-xl px-3 py-3 mb-1 ${errors.schoolSlug ? 'border-red-400' : 'border-gray-200'} bg-gray-50`}>
                  <Ionicons name="business-outline" size={18} color={COLORS.gray500} />
                  <TextInput
                    className="flex-1 ml-2 text-gray-700 text-sm"
                    value={value}
                    onChangeText={onChange}
                    placeholder="e.g. greenwood-school"
                    placeholderTextColor={COLORS.gray500}
                    autoCapitalize="none"
                    autoCorrect={false}
                  />
                </View>
              )}
            />
            {errors.schoolSlug && (
              <Text className="text-red-500 text-xs mb-3">{errors.schoolSlug.message}</Text>
            )}

            {/* Username */}
            <Text className="text-gray-600 text-sm font-medium mt-3 mb-1">Username / Email</Text>
            <Controller
              control={control}
              name="username"
              render={({ field: { onChange, value } }) => (
                <View className={`flex-row items-center border rounded-xl px-3 py-3 mb-1 ${errors.username ? 'border-red-400' : 'border-gray-200'} bg-gray-50`}>
                  <Ionicons name="person-outline" size={18} color={COLORS.gray500} />
                  <TextInput
                    className="flex-1 ml-2 text-gray-700 text-sm"
                    value={value}
                    onChangeText={onChange}
                    placeholder="username or email"
                    placeholderTextColor={COLORS.gray500}
                    autoCapitalize="none"
                    autoCorrect={false}
                    keyboardType="email-address"
                  />
                </View>
              )}
            />
            {errors.username && (
              <Text className="text-red-500 text-xs mb-3">{errors.username.message}</Text>
            )}

            {/* Password */}
            <Text className="text-gray-600 text-sm font-medium mt-3 mb-1">Password</Text>
            <Controller
              control={control}
              name="password"
              render={({ field: { onChange, value } }) => (
                <View className={`flex-row items-center border rounded-xl px-3 py-3 mb-1 ${errors.password ? 'border-red-400' : 'border-gray-200'} bg-gray-50`}>
                  <Ionicons name="lock-closed-outline" size={18} color={COLORS.gray500} />
                  <TextInput
                    className="flex-1 ml-2 text-gray-700 text-sm"
                    value={value}
                    onChangeText={onChange}
                    placeholder="Enter password"
                    placeholderTextColor={COLORS.gray500}
                    secureTextEntry={!showPassword}
                  />
                  <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                    <Ionicons
                      name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                      size={18}
                      color={COLORS.gray500}
                    />
                  </TouchableOpacity>
                </View>
              )}
            />
            {errors.password && (
              <Text className="text-red-500 text-xs mb-3">{errors.password.message}</Text>
            )}

            {/* Forgot password */}
            <TouchableOpacity className="self-end mt-1 mb-6" onPress={() => router.push('/(auth)/forgot-password')}>
              <Text className="text-primary-600 text-sm font-medium">Forgot Password?</Text>
            </TouchableOpacity>

            {/* Submit */}
            <TouchableOpacity
              onPress={handleSubmit(onSubmit)}
              disabled={isSubmitting}
              className={`rounded-xl py-4 items-center ${isSubmitting ? 'bg-primary-300' : 'bg-primary-700'}`}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text className="text-white font-semibold text-base">Sign In</Text>
              )}
            </TouchableOpacity>

            {/* OTP option */}
            <View className="flex-row justify-center mt-6">
              <Text className="text-gray-500 text-sm">Prefer OTP login? </Text>
              <TouchableOpacity onPress={() => router.push('/(auth)/otp')}>
                <Text className="text-primary-600 text-sm font-medium">Sign in with OTP</Text>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
