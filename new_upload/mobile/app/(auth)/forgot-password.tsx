import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, KeyboardAvoidingView,
  Platform, ScrollView, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import { authService } from '@/services/auth.service';
import { COLORS } from '@/constants';

export default function ForgotPasswordScreen() {
  const [email,   setEmail]   = useState('');
  const [loading, setLoading] = useState(false);
  const [sent,    setSent]    = useState(false);

  const handleSend = async () => {
    if (!email.trim()) {
      Toast.show({ type: 'error', text1: 'Enter your email address' });
      return;
    }
    setLoading(true);
    try {
      await authService.forgotPassword(email.trim());
      setSent(true);
    } catch (err: any) {
      Toast.show({ type: 'error', text1: 'Failed', text2: err?.response?.data?.detail ?? 'Could not send reset email' });
    } finally { setLoading(false); }
  };

  return (
    <SafeAreaView className="flex-1 bg-white">
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} className="flex-1">
        <ScrollView contentContainerStyle={{ flexGrow: 1, padding: 24 }} keyboardShouldPersistTaps="handled">
          <TouchableOpacity onPress={() => router.back()} className="mb-6">
            <Ionicons name="arrow-back" size={24} color={COLORS.gray700} />
          </TouchableOpacity>

          {sent ? (
            <View className="flex-1 items-center justify-center">
              <Ionicons name="checkmark-circle" size={72} color={COLORS.success} />
              <Text className="text-2xl font-bold text-gray-800 mt-4">Email Sent!</Text>
              <Text className="text-gray-400 text-sm text-center mt-2">
                Check {email} for a password reset link.
              </Text>
              <TouchableOpacity className="mt-8 px-8 py-3 bg-primary-700 rounded-xl" onPress={() => router.replace('/(auth)/login')}>
                <Text className="text-white font-semibold">Back to Login</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <Text className="text-2xl font-bold text-gray-800 mb-1">Forgot Password?</Text>
              <Text className="text-gray-400 text-sm mb-8">
                Enter your registered email. We'll send you a password reset link.
              </Text>
              <Text className="text-gray-600 text-sm font-medium mb-1">Email Address</Text>
              <TextInput
                className="border border-gray-200 rounded-xl px-4 py-3 mb-6 text-sm text-gray-700 bg-gray-50"
                value={email} onChangeText={setEmail}
                keyboardType="email-address" autoCapitalize="none" autoCorrect={false}
                placeholder="your@email.com" placeholderTextColor={COLORS.gray500}
              />
              <TouchableOpacity
                onPress={handleSend} disabled={loading}
                className={`rounded-xl py-4 items-center ${loading ? 'bg-primary-300' : 'bg-primary-700'}`}
              >
                {loading ? <ActivityIndicator color="#fff" /> : <Text className="text-white font-semibold text-base">Send Reset Link</Text>}
              </TouchableOpacity>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
