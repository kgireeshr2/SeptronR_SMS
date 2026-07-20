import api from './axios';

export interface SchoolOverview {
  id: string;
  name: string;
  code: string;
  is_active: boolean;
  email?: string;
  phone?: string;
  city?: string;
  state?: string;
  country?: string;
  total_students?: number;
  total_staff?: number;
  created_at: string;
  subscription?: {
    plan_name: string;
    expires_at: string;
    is_active: boolean;
  };
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  description?: string;
  price_monthly: number;
  price_annual: number;
  max_students: number;
  max_staff: number;
  features: string[];
  is_active: boolean;
}

export interface SubscriptionPlanCreate {
  name: string;
  description?: string;
  price_monthly: number;
  price_annual: number;
  max_students: number;
  max_staff: number;
  features?: string[];
}

export interface SchoolSubscription {
  id: string;
  school_id: string;
  school_name?: string;
  plan_id: string;
  plan_name?: string;
  start_date: string;
  expires_at: string;
  is_active: boolean;
  billing_cycle: 'monthly' | 'annual';
  amount_paid: number;
}

export interface SchoolSubscriptionCreate {
  school_id: string;
  plan_id: string;
  start_date: string;
  expires_at: string;
  billing_cycle: 'monthly' | 'annual';
  amount_paid: number;
}

export interface FeatureFlag {
  id: string;
  school_id: string;
  feature_key: string;
  is_enabled: boolean;
  updated_at?: string;
}

export interface ImpersonationLog {
  id: string;
  super_admin_id: string;
  target_school_id: string;
  target_user_id?: string;
  target_school_name?: string;
  access_token: string;
  started_at: string;
  expires_at: string;
  reason?: string;
}

export const superAdminApi = {
  // Schools
  listSchools: () => api.get<SchoolOverview[]>('/superadmin/schools'),
  toggleSchool: (schoolId: string, isActive: boolean) =>
    api.patch(`/superadmin/schools/${schoolId}/toggle-active`, null, {
      params: { is_active: isActive },
    }),
  bootstrapSchool: (data: {
    school_name: string;
    school_code: string;
    admin_email: string;
    admin_password: string;
    admin_first_name: string;
    admin_last_name: string;
  }) => api.post<SchoolOverview>('/superadmin/bootstrap-school', data),

  // Subscription Plans
  listPlans: () => api.get<SubscriptionPlan[]>('/superadmin/plans'),
  createPlan: (data: SubscriptionPlanCreate) =>
    api.post<SubscriptionPlan>('/superadmin/plans', data),
  updatePlan: (planId: string, data: Partial<SubscriptionPlanCreate>) =>
    api.put<SubscriptionPlan>(`/superadmin/plans/${planId}`, data),

  // Subscriptions
  listSubscriptions: (schoolId?: string) =>
    api.get<SchoolSubscription[]>('/superadmin/subscriptions', {
      params: schoolId ? { school_id: schoolId } : {},
    }),
  createSubscription: (data: SchoolSubscriptionCreate) =>
    api.post<SchoolSubscription>('/superadmin/subscriptions', data),
  deactivateSubscription: (subId: string) =>
    api.patch(`/superadmin/subscriptions/${subId}/deactivate`),

  // Feature Flags
  getFeatureFlags: (schoolId: string) =>
    api.get<FeatureFlag[]>(`/superadmin/schools/${schoolId}/features`),
  setFeatureFlag: (schoolId: string, featureKey: string, isEnabled: boolean) =>
    api.put(`/superadmin/schools/${schoolId}/features`, {
      feature_key: featureKey,
      is_enabled: isEnabled,
    }),

  // Impersonation
  impersonate: (schoolId: string, reason?: string) =>
    api.post<ImpersonationLog>('/superadmin/impersonate', {
      school_id: schoolId,
      reason,
    }),
};
