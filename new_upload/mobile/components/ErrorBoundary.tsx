import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Sentry from '@sentry/react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '@/constants';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError:    boolean;
  error:       Error | null;
  errorInfo:   ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    Sentry.captureException(error, { extra: { componentStack: errorInfo.componentStack } });
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
          <ScrollView contentContainerStyle={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 }}>
            <Ionicons name="bug-outline" size={64} color={COLORS.danger} />
            <Text style={{ fontSize: 20, fontWeight: 'bold', color: '#1f2937', marginTop: 16 }}>
              Something went wrong
            </Text>
            <Text style={{ fontSize: 14, color: '#6b7280', textAlign: 'center', marginTop: 8 }}>
              An unexpected error occurred. Our team has been notified.
            </Text>
            {__DEV__ && this.state.error && (
              <View style={{ backgroundColor: '#fef2f2', borderRadius: 8, padding: 12, marginTop: 16, width: '100%' }}>
                <Text style={{ color: '#b91c1c', fontSize: 12, fontFamily: 'monospace' }} numberOfLines={10}>
                  {this.state.error.toString()}
                </Text>
              </View>
            )}
            <TouchableOpacity
              onPress={this.handleReset}
              style={{ backgroundColor: COLORS.primary, borderRadius: 12, paddingHorizontal: 32, paddingVertical: 12, marginTop: 24 }}
            >
              <Text style={{ color: '#fff', fontWeight: '600' }}>Try Again</Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      );
    }

    return this.props.children;
  }
}
