import React from 'react';
import { View, Text } from 'react-native';
import { COLORS } from '@/constants';

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'default';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  small?: boolean;
}

const variantStyles: Record<BadgeVariant, { bg: string; text: string }> = {
  success: { bg: '#dcfce7', text: '#15803d' },
  warning: { bg: '#fef9c3', text: '#a16207' },
  danger:  { bg: '#fee2e2', text: '#b91c1c' },
  info:    { bg: '#e0f2fe', text: '#0369a1' },
  default: { bg: '#f3f4f6', text: '#374151' },
};

export function Badge({ label, variant = 'default', small = false }: BadgeProps) {
  const { bg, text } = variantStyles[variant];
  return (
    <View style={{ backgroundColor: bg, borderRadius: 9999, paddingHorizontal: small ? 8 : 12, paddingVertical: small ? 2 : 4 }}>
      <Text style={{ color: text, fontSize: small ? 10 : 12, fontWeight: '600' }}>
        {label}
      </Text>
    </View>
  );
}

export function feeStatusBadge(status: string): BadgeVariant {
  switch (status) {
    case 'paid':    return 'success';
    case 'overdue': return 'danger';
    case 'partial': return 'warning';
    default:        return 'info';
  }
}

export function leaveStatusBadge(status: string): BadgeVariant {
  switch (status) {
    case 'approved': return 'success';
    case 'rejected': return 'danger';
    default:         return 'warning';
  }
}

export function attendanceBadge(status: string): BadgeVariant {
  switch (status) {
    case 'present': return 'success';
    case 'absent':  return 'danger';
    case 'late':    return 'warning';
    case 'excused': return 'info';
    default:        return 'default';
  }
}
