import React, { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import api from '@/api/axios';

type Category = 'general' | 'admission' | 'attendance' | 'fees' | 'exam' | 'library' | 'communication' | 'security';

const CATEGORIES: { key: Category; label: string }[] = [
  { key: 'general', label: 'General' },
  { key: 'admission', label: 'Admission' },
  { key: 'attendance', label: 'Attendance' },
  { key: 'fees', label: 'Fees' },
  { key: 'exam', label: 'Exam' },
  { key: 'library', label: 'Library' },
  { key: 'communication', label: 'Communication' },
  { key: 'security', label: 'Security' },
];

const FIELDS: Record<Category, { key: string; label: string; type: string; placeholder?: string }[]> = {
  general: [
    { key: 'school_name', label: 'School Name', type: 'text' },
    { key: 'tagline', label: 'Tagline', type: 'text' },
    { key: 'timezone', label: 'Timezone', type: 'text', placeholder: 'Asia/Kolkata' },
    { key: 'currency', label: 'Currency', type: 'text', placeholder: 'INR' },
    { key: 'date_format', label: 'Date Format', type: 'text', placeholder: 'DD/MM/YYYY' },
    { key: 'academic_start_month', label: 'Academic Start Month (1-12)', type: 'number' },
    { key: 'primary_color', label: 'Primary Color', type: 'color' },
    { key: 'school_website', label: 'School Website', type: 'url' },
  ],
  admission: [
    { key: 'admission_number_prefix', label: 'Admission Number Prefix', type: 'text', placeholder: 'STU' },
    { key: 'admission_number_start', label: 'Start Number', type: 'number' },
    { key: 'admission_number_format', label: 'Number Format', type: 'text', placeholder: '{PREFIX}-{YEAR}-{SEQ:04d}' },
    { key: 'auto_create_student_on_approval', label: 'Auto Create Student on Approval', type: 'toggle' },
  ],
  attendance: [
    { key: 'low_attendance_threshold_pct', label: 'Low Attendance Threshold (%)', type: 'number' },
    { key: 'absent_notify_delay_minutes', label: 'Absent Notify Delay (minutes)', type: 'number' },
    { key: 'notify_parents_sms', label: 'Notify Parents via SMS', type: 'toggle' },
    { key: 'notify_parents_whatsapp', label: 'Notify Parents via WhatsApp', type: 'toggle' },
    { key: 'mark_attendance_before_minutes', label: 'Allow Marking Before (minutes)', type: 'number' },
  ],
  fees: [
    { key: 'fine_enabled', label: 'Late Fine Enabled', type: 'toggle' },
    { key: 'fine_per_day_paise', label: 'Fine Per Day (paise)', type: 'number' },
    { key: 'receipt_number_prefix', label: 'Receipt Number Prefix', type: 'text', placeholder: 'RCP' },
    { key: 'receipt_number_start', label: 'Receipt Start Number', type: 'number' },
    { key: 'due_reminder_days_before', label: 'Due Reminder Days Before', type: 'number' },
    { key: 'late_fee_grace_days', label: 'Late Fee Grace Days', type: 'number' },
    { key: 'online_payment_enabled', label: 'Online Payment Enabled', type: 'toggle' },
    { key: 'razorpay_key_id', label: 'Razorpay Key ID', type: 'text' },
    { key: 'razorpay_key_secret', label: 'Razorpay Key Secret', type: 'password' },
  ],
  exam: [
    { key: 'default_pass_percentage', label: 'Default Pass Percentage', type: 'number' },
    { key: 'result_sms_on_publish', label: 'Send SMS on Result Publish', type: 'toggle' },
    { key: 'show_rank_on_report_card', label: 'Show Rank on Report Card', type: 'toggle' },
    { key: 'show_attendance_on_report_card', label: 'Show Attendance on Report Card', type: 'toggle' },
    { key: 'report_card_footer_text', label: 'Report Card Footer Text', type: 'textarea' },
  ],
  library: [
    { key: 'max_books_student', label: 'Max Books per Student', type: 'number' },
    { key: 'max_books_staff', label: 'Max Books per Staff', type: 'number' },
    { key: 'default_loan_days', label: 'Default Loan Days', type: 'number' },
    { key: 'fine_per_day_overdue_paise', label: 'Fine Per Day Overdue (paise)', type: 'number' },
    { key: 'overdue_reminder_frequency_days', label: 'Overdue Reminder Every (days)', type: 'number' },
  ],
  communication: [
    { key: 'sms_gateway', label: 'SMS Gateway', type: 'text', placeholder: 'msg91' },
    { key: 'sms_api_key', label: 'SMS API Key', type: 'password' },
    { key: 'sms_sender_id', label: 'SMS Sender ID', type: 'text' },
    { key: 'sms_template_id', label: 'SMS DLT Template ID', type: 'text' },
    { key: 'whatsapp_enabled', label: 'WhatsApp Enabled', type: 'toggle' },
    { key: 'whatsapp_token', label: 'WhatsApp Token (Meta)', type: 'password' },
    { key: 'whatsapp_phone_id', label: 'WhatsApp Phone Number ID', type: 'text' },
    { key: 'email_backend', label: 'Email Backend', type: 'text', placeholder: 'smtp' },
    { key: 'smtp_host', label: 'SMTP Host', type: 'text' },
    { key: 'smtp_port', label: 'SMTP Port', type: 'number' },
    { key: 'smtp_username', label: 'SMTP Username', type: 'text' },
    { key: 'smtp_password', label: 'SMTP Password', type: 'password' },
    { key: 'smtp_from_email', label: 'SMTP From Email', type: 'email' },
    { key: 'smtp_from_name', label: 'SMTP From Name', type: 'text' },
    { key: 'smtp_use_tls', label: 'Use TLS', type: 'toggle' },
  ],
  security: [
    { key: 'password_min_length', label: 'Minimum Password Length', type: 'number' },
    { key: 'password_require_uppercase', label: 'Require Uppercase', type: 'toggle' },
    { key: 'password_require_number', label: 'Require Number', type: 'toggle' },
    { key: 'password_require_symbol', label: 'Require Symbol', type: 'toggle' },
    { key: 'session_timeout_minutes', label: 'Session Timeout (minutes)', type: 'number' },
    { key: 'max_login_attempts', label: 'Max Login Attempts', type: 'number' },
  ],
};

const Page: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<Category>('general');
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const loadCategory = useCallback(async (cat: Category) => {
    setLoading(true);
    try {
      const r = await api.get(`/settings/${cat}`);
      setValues((r as any) ?? {});
    } catch { setValues({}); } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadCategory(activeCategory); }, [activeCategory]);

  const handleChange = (key: string, value: string) => {
    setValues(p => ({ ...p, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/settings/${activeCategory}`, values);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const fields = FIELDS[activeCategory] ?? [];

  return (
    <div>
      <PageHeader title="School Settings" />
      <div className="flex gap-6">
        {/* Sidebar */}
        <aside className="w-52 flex-shrink-0">
          <nav className="space-y-1">
            {CATEGORIES.map(c => (
              <button
                key={c.key}
                onClick={() => setActiveCategory(c.key)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors ${
                  activeCategory === c.key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                {c.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Form */}
        <div className="flex-1">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-5 text-base font-semibold capitalize text-gray-900 dark:text-white">
              {CATEGORIES.find(c => c.key === activeCategory)?.label} Settings
            </h3>

            {loading ? (
              <p className="text-center text-gray-500 py-8">Loading...</p>
            ) : (
              <div className="space-y-4">
                {fields.map(field => (
                  <div key={field.key}>
                    <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {field.label}
                    </label>

                    {field.type === 'toggle' ? (
                      <label className="flex cursor-pointer items-center gap-3">
                        <div className="relative">
                          <input
                            type="checkbox"
                            className="sr-only"
                            checked={values[field.key] === 'true'}
                            onChange={e => handleChange(field.key, e.target.checked ? 'true' : 'false')}
                          />
                          <div className={`h-6 w-11 rounded-full transition-colors ${
                            values[field.key] === 'true' ? 'bg-blue-600' : 'bg-gray-300'
                          }`} />
                          <div className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                            values[field.key] === 'true' ? 'translate-x-5' : 'translate-x-0.5'
                          }`} />
                        </div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {values[field.key] === 'true' ? 'Enabled' : 'Disabled'}
                        </span>
                      </label>
                    ) : field.type === 'textarea' ? (
                      <textarea
                        rows={3}
                        value={values[field.key] ?? ''}
                        placeholder={field.placeholder}
                        onChange={e => handleChange(field.key, e.target.value)}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                      />
                    ) : field.type === 'color' ? (
                      <div className="flex items-center gap-3">
                        <input
                          type="color"
                          value={values[field.key] ?? '#1a56db'}
                          onChange={e => handleChange(field.key, e.target.value)}
                          className="h-9 w-14 rounded-lg border border-gray-300 cursor-pointer"
                        />
                        <span className="text-sm text-gray-500 font-mono">{values[field.key] ?? '#1a56db'}</span>
                      </div>
                    ) : (
                      <input
                        type={field.type}
                        value={values[field.key] ?? ''}
                        placeholder={field.placeholder}
                        onChange={e => handleChange(field.key, e.target.value)}
                        className="w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                      />
                    )}
                  </div>
                ))}

                <div className="flex items-center gap-3 pt-4 border-t border-gray-100 dark:border-gray-700">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                  {saved && (
                    <span className="text-sm text-green-600 font-medium">✓ Saved successfully</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Page;
