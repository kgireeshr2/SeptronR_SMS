import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, KeyboardAvoidingView,
  Platform, ScrollView, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import * as SecureStore from 'expo-secure-store';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/stores/authStore';
import { COLORS } from '@/constants';

type Step = 'request' | 'verify';

export default function OtpScreen() {
  const [step,       setStep]       = useState<Step>('request');
  const [schoolSlug, setSchoolSlug] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [otp,        setOtp]        = useState('');
  const [loading,    setLoading]    = useState(false);
  const { refreshUser } = useAuthStore();

  const sendOtp = async () => {
    if (!schoolSlug.trim() || !identifier.trim()) {
      Toast.show({ type: 'error', text1: 'Both fields required' });
      return;
    }
    setLoading(true);
    try {
      await authService.sendOtp(identifier.trim(), schoolSlug.trim());
      Toast.show({ type: 'success', text1: 'OTP Sent', text2: 'Check your email or phone.' });
      setStep('verify');
    } catch (err: any) {
      Toast.show({ type: 'error', text1: 'Failed', text2: err?.response?.data?.detail ?? 'Could not send OTP' });
    } finally { setLoading(false); }
  };

  const verifyOtp = async () => {
    if (!otp.trim()) {
      Toast.show({ type: 'error', text1: 'Enter OTP' });
      return;
    }
    setLoading(true);
    try {
      const data = await authService.verifyOtp(identifier.trim(), otp.trim(), schoolSlug.trim());
      // Store tokens directly
      await SecureStore.setItemAsync('sms_access_token',  data.accessToken);
      await SecureStore.setItemAsync('sms_refresh_token', data.refreshToken);
      await refreshUser();
      router.replace('/(app)/dashboard');
    } catch (err: any) {
      Toast.show({ type: 'error', text1: 'Invalid OTP', text2: err?.response?.data?.detail ?? 'Please try again' });
    } finally { setLoading(false); }
  };

  return (
    <SafeAreaView className="flex-1 bg-white">
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} className="flex-1">
        <ScrollView contentContainerStyle={{ flexGrow: 1, padding: 24 }} keyboardShouldPersistTaps="handled">
          <TouchableOpacity onPress={() => router.back()} className="mb-6">
            <Ionicons name="arrow-back" size={24} color={COLORS.gray700} />
          </TouchableOpacity>
          <Text className="text-2xl font-bold text-gray-800 mb-1">
            {step === 'request' ? 'OTP Login' : 'Enter OTP'}
          </Text>
          <Text className="text-gray-400 text-sm mb-8">
            {step === 'request'
              ? "We'll send a one-time password to your registered email or phone."
              : `Enter the 6-digit OTP sent to ${identifier}`}
          </Text>

          {step === 'request' ? (
            <>
              <Text className="text-gray-600 text-sm font-medium mb-1">School ID</Text>
              <TextInput
                className="border border-gray-200 rounded-xl px-4 py-3 mb-4 text-sm text-gray-700 bg-gray-50"
                value={schoolSlug} onChangeText={setSchoolSlug}
                placeholder="e.g. greenwood-school" autoCapitalize="none" autoCorrect={false}
              />
              <Text className="text-gray-600 text-sm font-medium mb-1">Email or Phone</Text>
              <TextInput
                className="border border-gray-200 rounded-xl px-4 py-3 mb-6 text-sm text-gray-700 bg-gray-50"
                value={identifier} onChangeText={setIdentifier}
                placeholder="email or phone" keyboardType="email-address" autoCapitalize="none"
              />
              <TouchableOpacity
                onPress={sendOtp} disabled={loading}
                className={`rounded-xl py-4 items-center ${loading ? 'bg-primary-300' : 'bg-primary-700'}`}
              >
                {loading ? <ActivityIndicator color="#fff" /> : <Text className="text-white font-semibold text-base">Send OTP</Text>}
              </TouchableOpacity>
            </>
          ) : (
            <>
              <Text className="text-gray-600 text-sm font-medium mb-1">6-digit OTP</Text>
              <TextInput
                className="border border-gray-200 rounded-xl px-4 py-3 mb-6 text-sm text-gray-700 bg-gray-50 text-center tracking-widest text-xl"
                value={otp} onChangeText={setOtp}
                keyboardType="number-pad" maxLength={6}
              />
              <TouchableOpacity
                onPress={verifyOtp} disabled={loading}
                className={`rounded-xl py-4 items-center ${loading ? 'bg-primary-300' : 'bg-primary-700'}`}
              >
                {loading ? <ActivityIndicator color="#fff" /> : <Text className="text-white font-semibold text-base">Verify OTP</Text>}
              </TouchableOpacity>
              <TouchableOpacity className="mt-4 items-center" onPress={() => setStep('request')}>
                <Text className="text-primary-600 text-sm">Resend OTP</Text>
              </TouchableOpacity>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
