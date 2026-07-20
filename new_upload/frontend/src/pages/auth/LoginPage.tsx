import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Eye, EyeOff, School } from 'lucide-react';
import { authApi } from '@api/auth';
import { useAuthStore } from '@store/authStore';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Determine redirect path based on user role slug (derived from permissions).
 * Super admins → /super-admin/dashboard
 * Admins/Principals → /dashboard
 * Teachers → /teacher/dashboard
 * Students → /student/portal
 * Parents → /parent/portal
 */
function getRoleBasedRedirect(permissions: string[], isSuperAdmin: boolean): string {
  if (isSuperAdmin) return '/super-admin/dashboard';
  // Simple heuristic: check what modules the user has access to
  const hasModule = (m: string) => permissions.some(p => p.startsWith(`${m}:`));
  if (hasModule('settings') || hasModule('roles')) return '/dashboard';
  if (hasModule('attendance') && hasModule('exams')) return '/teacher/dashboard';
  if (hasModule('homework') && !hasModule('staff')) return '/student/portal';
  if (hasModule('ptm') && !hasModule('staff')) return '/parent/portal';
  return '/dashboard';
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { accessToken, currentUser, setAccessToken, setUser } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ?? '';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({ resolver: zodResolver(loginSchema) });

  useEffect(() => {
    if (!accessToken) return;
    const destination = getRoleBasedRedirect(
      currentUser?.permissions ?? [],
      currentUser?.is_super_admin ?? false
    );
    navigate(destination, { replace: true });
  }, [accessToken, currentUser, navigate]);

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      const res = await authApi.login(data) as any;
      const { access_token, user, school } = res?.data ?? res;
      setAccessToken(access_token);
      setUser(user, school ?? null, user.permissions ?? []);
      if (school?.id) {
        localStorage.setItem('sms-school-id', school.id);
      }
      toast.success(`Welcome back, ${user.username ?? user.email}!`);
      const destination = from || getRoleBasedRedirect(user.permissions ?? [], user.is_super_admin);
      navigate(destination, { replace: true });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err as { message?: string })?.message ??
        'Invalid credentials';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 to-slate-700 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600 shadow-lg">
            <School size={32} className="text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-white">
            SeptroSchool
          </h1>
          <p className="mt-1 text-sm text-slate-400">Sign in to your account</p>
        </div>

        <div className="rounded-2xl bg-white p-8 shadow-2xl dark:bg-gray-800">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label
                htmlFor="username"
                className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Username / Email / Phone
              </label>
              <input
                id="username"
                type="text"
                {...register('username')}
                aria-invalid={!!errors.username}
                className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm outline-none transition-all focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                placeholder="admin@school.com"
                autoComplete="username"
              />
              {errors.username && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.username.message}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  {...register('password')}
                  aria-invalid={!!errors.password}
                  className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 pr-10 text-sm outline-none transition-all focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.password.message}
                </p>
              )}
            </div>

            <div className="flex justify-end">
              <Link
                to="/forgot-password"
                className="text-xs text-brand-600 hover:underline"
              >
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-semibold text-white transition-all hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-gray-400">
            Default Super Admin:{' '}
            <strong className="text-gray-600">superadmin</strong> /{' '}
            <strong className="text-gray-600">SuperAdmin@123</strong>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
