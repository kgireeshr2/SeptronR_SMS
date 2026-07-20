import React from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { websiteApi } from '@api/website';
import { useSchoolSite } from '@hooks/useSchoolSite';

const EnquiryForm: React.FC = () => {
  const { slug } = useSchoolSite();
  const [done, setDone] = React.useState(false);
  const [form, setForm] = React.useState({ name: '', phone: '', email: '', subject: '', message: '' });

  const mutation = useMutation({
    mutationFn: () => {
      const body: Record<string, string> = { name: form.name, message: form.message };
      if (form.phone) body.phone = form.phone;
      if (form.email) body.email = form.email;
      if (form.subject) body.subject = form.subject;
      return websiteApi.submitEnquiry(slug, body);
    },
    onSuccess: () => {
      setDone(true);
      toast.success('Your enquiry has been submitted.');
    },
    onError: (err: any) => toast.error(err?.detail ?? err?.message ?? 'Submission failed'),
  });

  if (done) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-5 text-sm text-green-700">
        Thank you! We have received your enquiry and will get back to you soon.
      </div>
    );
  }

  const input = 'w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2';
  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        <input
          className={input}
          placeholder="Your Name *"
          value={form.name}
          onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
        />
        <input
          className={input}
          placeholder="Phone"
          value={form.phone}
          onChange={(e) => setForm((p) => ({ ...p, phone: e.target.value }))}
        />
        <input
          className={input}
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
        />
        <input
          className={input}
          placeholder="Subject"
          value={form.subject}
          onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))}
        />
      </div>
      <textarea
        className={input}
        rows={5}
        placeholder="Your Message *"
        value={form.message}
        onChange={(e) => setForm((p) => ({ ...p, message: e.target.value }))}
      />
      <button
        disabled={mutation.isPending}
        onClick={() => {
          if (!form.name.trim() || !form.message.trim()) {
            toast.error('Please enter your name and message.');
            return;
          }
          mutation.mutate();
        }}
        className="rounded-md px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
        style={{ background: 'var(--site-primary)' }}
      >
        {mutation.isPending ? 'Submitting…' : 'Submit Enquiry'}
      </button>
    </div>
  );
};

export default EnquiryForm;
