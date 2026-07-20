import React, { useState, useEffect, useCallback, useRef } from 'react';
import { PageHeader } from '@components/shared/PageHeader';
import { templatesApi } from '@/api/templates';
import { communicationsApi, type NotificationTemplate } from '@/api/communications';
import { toast } from 'sonner';
import { formatDate } from '@utils/formatters';

interface DocumentTemplate {
  id: string;
  template_name: string;
  template_type: string;
  template_html?: string;
  canvas_width_mm?: number;
  canvas_height_mm?: number;
  description?: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

// Actual DB enum values for document template types
const DOC_TEMPLATE_TYPES: { value: string; label: string }[] = [
  { value: 'student_id_front',      label: 'Student ID Front' },
  { value: 'student_id_back',       label: 'Student ID Back' },
  { value: 'staff_id_front',        label: 'Staff ID Front' },
  { value: 'staff_id_back',         label: 'Staff ID Back' },
  { value: 'admit_card',            label: 'Admit Card' },
  { value: 'fee_receipt',           label: 'Fee Receipt' },
  { value: 'report_card',           label: 'Report Card' },
  { value: 'transfer_certificate',  label: 'Transfer Cert.' },
  { value: 'bonafide_certificate',  label: 'Bonafide Cert.' },
  { value: 'character_certificate', label: 'Character Cert.' },
  { value: 'payslip',               label: 'Payslip' },
  { value: 'custom',                label: 'Custom' },
];

const NOTIFICATION_TRIGGERS: { value: string; label: string }[] = [
  { value: 'attendance_absent', label: 'Attendance Absent' },
  { value: 'fee_due',           label: 'Fee Due' },
  { value: 'fee_receipt',       label: 'Fee Receipt' },
  { value: 'result_published',  label: 'Result Published' },
  { value: 'homework_assigned', label: 'Homework Assigned' },
  { value: 'ptm_reminder',      label: 'PTM Reminder' },
  { value: 'birthday',          label: 'Birthday' },
  { value: 'custom',            label: 'Custom' },
];

// ── Sample data for template preview ─────────────────────────────────────────
const SAMPLE_DATA: Record<string, string> = {
  // School
  school_name: 'Greenwood Academy',
  school_address: '123 Oak Street, Springfield – 560001',
  school_phone: '+91 98765 43210',
  school_email: 'info@greenwoodacademy.edu',
  school_reg_number: 'REG-2024-001',
  school_seal_url: '',
  // Student
  student_name: 'Arjun Kumar Sharma',
  admission_number: 'ADM-2024-0042',
  roll_number: '15',
  class_name: 'Class X',
  section_name: 'A',
  date_of_birth: '12 Mar 2010',
  admission_date: '01 Jun 2020',
  blood_group: 'O+',
  academic_year: '2025–2026',
  photo_url: 'https://placehold.co/120x150/4f86c6/fff?text=Photo',
  qr_code_url: 'https://placehold.co/80x80/333/fff?text=QR',
  address: '45 Maple Road',
  city: 'Springfield',
  pincode: '560001',
  father_name: 'Mr. Rajesh Sharma',
  father_phone: '+91 98001 11222',
  mother_name: 'Mrs. Priya Sharma',
  mother_phone: '+91 98001 33444',
  // Staff
  staff_name: 'Ms. Anjali Verma',
  designation: 'Senior Teacher',
  department: 'Science',
  employee_id: 'EMP-2019-015',
  joining_date: '01 Jul 2019',
  qualification: 'M.Sc., B.Ed.',
  emergency_contact: '+91 99887 76655',
  valid_from: 'Apr 2025',
  valid_until: 'Mar 2026',
  pan_number: 'ABCDE1234F',
  pf_number: 'PF/KA/12345',
  bank_account: 'XXXX XXXX 7890',
  // Exam / Admit card
  exam_name: 'Annual Examination 2026',
  // Fee receipt
  receipt_number: 'RCPT-2026-00892',
  payment_date: '15 Apr 2026',
  total_amount: '12,500',
  payment_mode: 'UPI',
  transaction_ref: 'TXN2026041500892',
  // Report card
  total_marks_obtained: '487',
  total_max_marks: '500',
  percentage: '97.4',
  overall_grade: 'A+',
  result_status: 'PASS',
  rank: '1',
  attendance_percentage: '96.5',
  // TC
  tc_number: 'TC-2026-0087',
  issue_date: '21 Apr 2026',
  class_last_studied: 'X – A',
  date_of_leaving: '20 Apr 2026',
  reason_for_leaving: 'Transfer',
  character_and_conduct: 'Good',
  attendance_record: '224 / 240 days',
  eligible_for_readmission: 'Yes',
  // Bonafide / Char cert
  purpose: 'Bank Account Opening',
  conduct: 'Exemplary',
  // Payslip
  pay_month: 'April',
  pay_year: '2026',
  days_worked: '26',
  total_days: '30',
  gross_salary: '65,000',
  total_deductions: '9,750',
  net_salary: '55,250',
  net_salary_words: 'Fifty-Five Thousand Two Hundred and Fifty Only',
  // Custom
  document_title: 'Official Notice',
  document_body: 'This is a sample document body with placeholder content for preview purposes. You can customize this template with your own content and variables.',
  notice_subject: 'Important School Notice',
  notice_body: 'Please be informed of the upcoming school event scheduled for next week.',
};

// Replace Jinja2 {{ var }} and simple {% for %} / {% endfor %} loops
function renderPreviewHtml(html: string): string {
  if (!html) return '<p style="padding:20px;color:#888;">No HTML content defined for this template.</p>';

  // Replace {% for subject in subjects %} ... {% endfor %} with 3 sample rows
  const subjectRows = `
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">Mathematics</td><td style="padding:2mm;text-align:center;">100</td><td style="padding:2mm;text-align:center;">94</td><td style="padding:2mm;text-align:center;">A+</td><td style="padding:2mm;text-align:center;"></td><td style="padding:2mm;text-align:center;">94%</td><td style="padding:2mm;text-align:center;">Excellent</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">Science</td><td style="padding:2mm;text-align:center;">100</td><td style="padding:2mm;text-align:center;">89</td><td style="padding:2mm;text-align:center;">A</td><td style="padding:2mm;text-align:center;"></td><td style="padding:2mm;text-align:center;">89%</td><td style="padding:2mm;text-align:center;">Very Good</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">English</td><td style="padding:2mm;text-align:center;">100</td><td style="padding:2mm;text-align:center;">92</td><td style="padding:2mm;text-align:center;">A+</td><td style="padding:2mm;text-align:center;"></td><td style="padding:2mm;text-align:center;">92%</td><td style="padding:2mm;text-align:center;">Excellent</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">Social Studies</td><td style="padding:2mm;text-align:center;">100</td><td style="padding:2mm;text-align:center;">86</td><td style="padding:2mm;text-align:center;">A</td><td style="padding:2mm;text-align:center;"></td><td style="padding:2mm;text-align:center;">86%</td><td style="padding:2mm;text-align:center;">Good</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">Hindi</td><td style="padding:2mm;text-align:center;">100</td><td style="padding:2mm;text-align:center;">88</td><td style="padding:2mm;text-align:center;">A</td><td style="padding:2mm;text-align:center;"></td><td style="padding:2mm;text-align:center;">88%</td><td style="padding:2mm;text-align:center;">Good</td></tr>`;

  const examRows = `
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">Mathematics</td><td style="padding:2mm;text-align:center;">28 Apr 2026</td><td style="padding:2mm;text-align:center;">Monday</td><td style="padding:2mm;text-align:center;">9:00 – 12:00</td><td style="padding:2mm;text-align:center;">101</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">Science</td><td style="padding:2mm;text-align:center;">30 Apr 2026</td><td style="padding:2mm;text-align:center;">Wednesday</td><td style="padding:2mm;text-align:center;">9:00 – 12:00</td><td style="padding:2mm;text-align:center;">102</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2mm;">English</td><td style="padding:2mm;text-align:center;">02 May 2026</td><td style="padding:2mm;text-align:center;">Friday</td><td style="padding:2mm;text-align:center;">9:00 – 12:00</td><td style="padding:2mm;text-align:center;">103</td></tr>`;

  const feeRows = `
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2.5mm;">Tuition Fee</td><td style="padding:2.5mm;text-align:right;">8,000</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2.5mm;">Development Fee</td><td style="padding:2.5mm;text-align:right;">2,500</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2.5mm;">Sports Fee</td><td style="padding:2.5mm;text-align:right;">1,500</td></tr>
    <tr style="border-bottom:0.3mm solid #ddd;"><td style="padding:2.5mm;">Computer Lab Fee</td><td style="padding:2.5mm;text-align:right;">500</td></tr>`;

  const earningsRows = `
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">Basic Salary</td><td style="padding:2mm;text-align:right;">40,000</td></tr>
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">HRA</td><td style="padding:2mm;text-align:right;">16,000</td></tr>
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">Conveyance</td><td style="padding:2mm;text-align:right;">4,500</td></tr>
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">Medical</td><td style="padding:2mm;text-align:right;">1,250</td></tr>
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">Special Allowance</td><td style="padding:2mm;text-align:right;">3,250</td></tr>`;

  const deductionsRows = `
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">PF (Employee)</td><td style="padding:2mm;text-align:right;">4,800</td></tr>
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">Professional Tax</td><td style="padding:2mm;text-align:right;">200</td></tr>
    <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">Income Tax (TDS)</td><td style="padding:2mm;text-align:right;">4,750</td></tr>`;

  let result = html;

  // Remove Jinja2 conditional blocks
  result = result.replace(/\{%[-\s]*if [^%]*%\}[\s\S]*?\{%[-\s]*endif[-\s]*%\}/g, '');
  result = result.replace(/\{%[-\s]*(?:else|elif[^%]*)[-\s]*%\}/g, '');

  // Replace for loops with sample rows
  result = result.replace(/\{%[-\s]*for s in subjects[-\s]*%\}[\s\S]*?\{%[-\s]*endfor[-\s]*%\}/gi, subjectRows);
  result = result.replace(/\{%[-\s]*for [a-z]+ in subjects[-\s]*%\}[\s\S]*?\{%[-\s]*endfor[-\s]*%\}/gi, subjectRows);
  result = result.replace(/\{%[-\s]*for [a-z]+ in exam_schedule[-\s]*%\}[\s\S]*?\{%[-\s]*endfor[-\s]*%\}/gi, examRows);
  result = result.replace(/\{%[-\s]*for item in fee_items[-\s]*%\}[\s\S]*?\{%[-\s]*endfor[-\s]*%\}/gi, feeRows);
  result = result.replace(/\{%[-\s]*for e in earnings[-\s]*%\}[\s\S]*?\{%[-\s]*endfor[-\s]*%\}/gi, earningsRows);
  result = result.replace(/\{%[-\s]*for d in deductions[-\s]*%\}[\s\S]*?\{%[-\s]*endfor[-\s]*%\}/gi, deductionsRows);
  // Any remaining for loops
  result = result.replace(/\{%[-\s]*for[^%]*%\}[\s\S]*?\{%[-\s]*endfor[-\s]*%\}/gi, '');
  // Remove remaining Jinja2 tags
  result = result.replace(/\{%[^%]*%\}/g, '');

  // Replace {{ variable.property }} e.g. s.subject_name → use key after dot
  result = result.replace(/\{\{\s*\w+\.(\w+)\s*\}\}/g, (_: string, prop: string) => {
    const keyMap: Record<string, string> = {
      subject_name: 'Mathematics', max_marks: '100', marks_obtained: '94',
      grade: 'A+', remarks: 'Excellent', percentage: '94',
      exam_date: '28 Apr 2026', day: 'Monday',
      start_time: '9:00 AM', end_time: '12:00 PM', room_number: '101',
      fee_head: 'Tuition Fee', amount: '8,000',
      component: 'Basic Salary',
    };
    return keyMap[prop] ?? prop;
  });

  // Replace {{ variable }} with sample data
  result = result.replace(/\{\{\s*([\w_]+)\s*\}\}/g, (_: string, key: string) => {
    return SAMPLE_DATA[key] ?? `[${key}]`;
  });

  return result;
}

// ── Template Preview Modal ────────────────────────────────────────────────────
const TemplatePreviewModal: React.FC<{
  template: DocumentTemplate;
  onClose: () => void;
}> = ({ template, onClose }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [zoom, setZoom] = useState(1);
  const [loadingFull, setLoadingFull] = useState(false);
  const [fullHtml, setFullHtml] = useState<string | null>(template.template_html ?? null);

  // Fetch full template (including HTML) if not already present
  useEffect(() => {
    if (fullHtml) return;
    setLoadingFull(true);
    templatesApi.get(template.id)
      .then((r: any) => setFullHtml(r?.data?.template_html ?? r?.template_html ?? ''))
      .catch(() => setFullHtml(''))
      .finally(() => setLoadingFull(false));
  }, [template.id, fullHtml]);

  const isCard = (template.canvas_width_mm ?? 90) <= 90;
  const w = template.canvas_width_mm ?? (isCard ? 85.6 : 210);
  const h = template.canvas_height_mm ?? (isCard ? 54 : 297);
  // Convert mm to px at 96dpi (1mm ≈ 3.7795px)
  const MM_TO_PX = 3.7795;
  const canvasW = Math.round(w * MM_TO_PX);
  const canvasH = Math.round(h * MM_TO_PX);

  const previewHtml = fullHtml !== null ? renderPreviewHtml(fullHtml) : '';

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-gray-900/95" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-gray-700 bg-gray-900 px-4 py-2.5">
        <div className="flex items-center gap-3">
          <button onClick={onClose} className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white" title="Close (Esc)">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
          <div>
            <div className="font-semibold text-white text-sm">{template.template_name}</div>
            <div className="text-xs text-gray-400">{w} × {h} mm &nbsp;·&nbsp; Preview with sample data</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom(z => Math.max(0.25, +(z - 0.25).toFixed(2)))} className="rounded px-2 py-1 text-sm text-gray-300 hover:bg-gray-700" title="Zoom out">−</button>
          <button onClick={() => setZoom(1)} className="rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-700">Reset</button>
          <button onClick={() => setZoom(z => Math.min(3, +(z + 0.25).toFixed(2)))} className="rounded px-2 py-1 text-sm text-gray-300 hover:bg-gray-700" title="Zoom in">+</button>
          <button
            onClick={() => setZoom(+(Math.min(window.innerWidth * 0.8 / canvasW, window.innerHeight * 0.75 / canvasH)).toFixed(2))}
            className="rounded px-2 py-1 text-xs text-gray-300 hover:bg-gray-700"
            title="Fit to screen"
          >
            Fit
          </button>
        </div>
      </div>

      {/* Canvas area */}
      <div className="flex flex-1 overflow-auto items-start justify-center p-8" style={{ backgroundColor: '#1a1a2e' }}>
        {loadingFull ? (
          <div className="flex items-center gap-2 text-gray-400 mt-32">
            <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
            Loading template...
          </div>
        ) : (
          <div
            style={{
              width: canvasW * zoom,
              height: canvasH * zoom,
              position: 'relative',
              boxShadow: '0 4px 40px rgba(0,0,0,0.7)',
              flexShrink: 0,
            }}
          >
            <iframe
              ref={iframeRef}
              srcDoc={previewHtml}
              title="Template Preview"
              sandbox="allow-same-origin"
              style={{
                width: canvasW,
                height: canvasH,
                border: 'none',
                background: '#fff',
                transform: `scale(${zoom})`,
                transformOrigin: 'top left',
                display: 'block',
              }}
            />
          </div>
        )}
      </div>

      {/* Footer hint */}
      <div className="border-t border-gray-700 bg-gray-900 px-4 py-1.5 text-center text-xs text-gray-500">
        Variables shown with sample data &nbsp;·&nbsp; Press <kbd className="rounded bg-gray-700 px-1 text-gray-300">Esc</kbd> to close
      </div>
    </div>
  );
};

// ── Bulk Print Modal ────────────────────────────────────────────────────────────
const BulkPrintModal: React.FC<{
  template: DocumentTemplate;
  onClose: () => void;
}> = ({ template, onClose }) => {
  const [classId, setClassId] = React.useState('');
  const [classes, setClasses] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [students, setStudents] = React.useState<any[]>([]);
  const [selectedIds, setSelectedIds] = React.useState<string[]>([]);

  React.useEffect(() => {
    import('@api/classes').then(({ classesApi }) =>
      classesApi.listClasses().then((r: any) => setClasses((r?.data ?? r) ?? []))
    );
  }, []);

  React.useEffect(() => {
    if (!classId) { setStudents([]); setSelectedIds([]); return; }
    import('@api/students').then(({ studentsApi }) =>
      studentsApi.list({ class_id: classId })
        .then((r: any) => {
          const s = (r?.data ?? r) ?? [];
          setStudents(s);
          setSelectedIds(s.map((x: any) => x.id));
        })
    );
  }, [classId]);

  const handlePrint = async () => {
    if (selectedIds.length === 0) {
      import('sonner').then(({ toast }) => toast.error('No students selected'));
      return;
    }

    // For id_card template type: use the dedicated bulk ID card endpoint
    if (template.template_type === 'id_card') {
      setLoading(true);
      try {
        const api = (await import('@api/axios')).default;
        const res = await api.post(
          '/students/id-cards/bulk',
          selectedIds,
          { responseType: 'blob' }
        );
        const url = URL.createObjectURL(new Blob([res as any], { type: 'application/pdf' }));
        const a = document.createElement('a'); a.href = url; a.download = 'id_cards_bulk.pdf'; a.click();
        URL.revokeObjectURL(url);
        onClose();
      } catch {
        import('sonner').then(({ toast }) => toast.error('Failed to generate ID cards'));
      } finally { setLoading(false); }
      return;
    }

    // For other templates: use the generic bulk_print endpoint
    setLoading(true);
    try {
      await templatesApi.bulkPrint({ template_id: template.id, record_ids: selectedIds });
      import('sonner').then(({ toast }) => toast.success(`Bulk print queued for ${selectedIds.length} records`));
      onClose();
    } catch {
      import('sonner').then(({ toast }) => toast.error('Failed to queue bulk print'));
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <h3 className="mb-4 text-lg font-semibold">Bulk Print — {template.template_name}</h3>
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium">Select Class</label>
          <select
            value={classId}
            onChange={(e) => setClassId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
          >
            <option value="">Select a class...</option>
            {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        {students.length > 0 && (
          <div className="mb-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm text-gray-600">{selectedIds.length} of {students.length} selected</span>
              <button
                onClick={() => setSelectedIds(selectedIds.length === students.length ? [] : students.map((s: any) => s.id))}
                className="text-xs text-brand-600 hover:underline"
              >
                {selectedIds.length === students.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1 rounded-lg border border-gray-200 p-2 dark:border-gray-700">
              {students.map((s: any) => (
                <label key={s.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(s.id)}
                    onChange={(e) => setSelectedIds((prev) =>
                      e.target.checked ? [...prev, s.id] : prev.filter((id) => id !== s.id)
                    )}
                    className="rounded"
                  />
                  <span className="text-sm">{s.first_name} {s.last_name}</span>
                  <span className="text-xs text-gray-400">{s.admission_number}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onClose} className="rounded-lg border px-4 py-2 text-sm">Cancel</button>
          <button
            onClick={handlePrint}
            disabled={loading || selectedIds.length === 0}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? 'Generating...' : `Print ${selectedIds.length} Records`}
          </button>
        </div>
      </div>
    </div>
  );
};

const Page: React.FC = () => {
  const [tab, setTab] = useState<'document' | 'notification'>('document');

  // ── Document Templates state ───────────────────────────────────────────
  const [templates, setTemplates] = useState<DocumentTemplate[]>([]);
  const [docLoading, setDocLoading] = useState(false);
  const [filterType, setFilterType] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState<DocumentTemplate | null>(null);
  const [form, setForm] = useState({
    template_name: '', template_type: 'custom',
    description: '', html_content: '', is_active: true,
  });
  const [bulkPrintTarget, setBulkPrintTarget] = useState<DocumentTemplate | null>(null);
  const [previewTarget, setPreviewTarget] = useState<DocumentTemplate | null>(null);

  // ── Notification Templates state ───────────────────────────────────────
  const [notifTemplates, setNotifTemplates] = useState<NotificationTemplate[]>([]);
  const [notifLoading, setNotifLoading] = useState(false);
  const [notifFilterTrigger, setNotifFilterTrigger] = useState('');
  const [showNotifModal, setShowNotifModal] = useState(false);
  const [editNotifTarget, setEditNotifTarget] = useState<NotificationTemplate | null>(null);
  const [notifForm, setNotifForm] = useState({
    name: '',
    event_trigger: 'custom',
    channels: ['in_app'] as string[],
    subject: '',
    body_template: '',
    is_active: true,
    is_default: false,
  });

  const loadTemplates = useCallback(async () => {
    setDocLoading(true);
    try {
      const r = await templatesApi.list({ template_type: filterType || undefined });
      const data = (r as any)?.data ?? r;
      setTemplates(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to load document templates', e);
    } finally { setDocLoading(false); }
  }, [filterType]);

  const loadNotifTemplates = useCallback(async () => {
    setNotifLoading(true);
    try {
      const r = await communicationsApi.listTemplates();
      const data = (r as any)?.data ?? r;
      setNotifTemplates(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to load notification templates', e);
    } finally { setNotifLoading(false); }
  }, []);

  useEffect(() => { loadTemplates(); }, [loadTemplates]);
  useEffect(() => { loadNotifTemplates(); }, [loadNotifTemplates]);

  // ── Document template actions ──────────────────────────────────────────
  const openCreate = () => {
    setEditTarget(null);
    setForm({ template_name: '', template_type: 'custom', description: '', html_content: '', is_active: true });
    setShowModal(true);
  };

  const openEdit = (t: DocumentTemplate) => {
    setEditTarget(t);
    setForm({ template_name: t.template_name, template_type: t.template_type, description: t.description ?? '', html_content: '', is_active: t.is_active });
    setShowModal(true);
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editTarget) { await templatesApi.update(editTarget.id, form); }
      else { await templatesApi.create(form); }
      setShowModal(false);
      loadTemplates();
    } catch { toast.error('Failed to save template'); }
  };

  const setDefault = async (id: string) => {
    await templatesApi.setDefault(id);
    loadTemplates();
  };

  const remove = async (id: string) => {
    if (!confirm('Delete this template?')) return;
    await templatesApi.delete(id);
    loadTemplates();
  };

  // ── Notification template actions ──────────────────────────────────────
  const openCreateNotif = () => {
    setEditNotifTarget(null);
    setNotifForm({ name: '', event_trigger: 'custom', channels: ['in_app'], subject: '', body_template: '', is_active: true, is_default: false });
    setShowNotifModal(true);
  };

  const openEditNotif = (t: NotificationTemplate) => {
    setEditNotifTarget(t);
    setNotifForm({ name: t.name, event_trigger: t.event_trigger, channels: t.channels ?? ['in_app'], subject: t.subject ?? '', body_template: t.body_template, is_active: t.is_active, is_default: t.is_default });
    setShowNotifModal(true);
  };

  const saveNotif = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editNotifTarget) { await communicationsApi.updateTemplate(editNotifTarget.id, notifForm as any); }
      else { await communicationsApi.createTemplate(notifForm as any); }
      setShowNotifModal(false);
      loadNotifTemplates();
    } catch { toast.error('Failed to save notification template'); }
  };

  const setDefaultNotif = async (id: string) => {
    try {
      await communicationsApi.setDefaultTemplate(id);
      toast.success('Default template updated');
      loadNotifTemplates();
    } catch { toast.error('Failed to set default'); }
  };

  const removeNotif = async (id: string) => {
    if (!confirm('Delete this notification template?')) return;
    try {
      await communicationsApi.deleteTemplate(id);
      loadNotifTemplates();
    } catch { toast.error('Failed to delete'); }
  };

  // ── Filtered notification templates ───────────────────────────────────
  const filteredNotif = notifFilterTrigger
    ? notifTemplates.filter(t => t.event_trigger === notifFilterTrigger)
    : notifTemplates;

  // ── Group notification templates by trigger ────────────────────────────
  const notifByTrigger = filteredNotif.reduce<Record<string, NotificationTemplate[]>>((acc, t) => {
    (acc[t.event_trigger] ??= []).push(t);
    return acc;
  }, {});

  const CHANNEL_LABELS: Record<string, string> = { in_app: 'In-App', email: 'Email', sms: 'SMS', whatsapp: 'WhatsApp', push: 'Push' };
  const CHANNEL_COLORS: Record<string, string> = { in_app: 'bg-purple-100 text-purple-700', email: 'bg-blue-100 text-blue-700', sms: 'bg-green-100 text-green-700', whatsapp: 'bg-emerald-100 text-emerald-700', push: 'bg-orange-100 text-orange-700' };

  return (
    <div>
      <PageHeader title="Templates" />

      {/* Tab switcher */}
      <div className="mb-5 flex border-b border-gray-200 dark:border-gray-700">
        {(['document', 'notification'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {t === 'document' ? 'Document Templates' : 'Notification Templates'}
            <span className="ml-1.5 rounded-full bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">
              {t === 'document' ? templates.length : notifTemplates.length}
            </span>
          </button>
        ))}
      </div>

      {/* ── DOCUMENT TEMPLATES TAB ───────────────────────────────────────── */}
      {tab === 'document' && (
        <>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setFilterType('')}
                className={`rounded-full px-3 py-1 text-xs font-medium border ${!filterType ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-300 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700'}`}
              >
                All
              </button>
              {DOC_TEMPLATE_TYPES.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setFilterType(value)}
                  className={`rounded-full px-3 py-1 text-xs font-medium border ${filterType === value ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-300 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700'}`}
                >
                  {label}
                </button>
              ))}
            </div>
            <button onClick={openCreate} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              + New Template
            </button>
          </div>

          {docLoading ? (
            <p className="py-12 text-center text-gray-500">Loading...</p>
          ) : templates.length === 0 ? (
            <div className="rounded-xl border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
              <p className="text-gray-500">No document templates found.</p>
            </div>
          ) : (
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    {['Name', 'Type', 'Default', 'Active', 'Created', 'Actions'].map(h => (
                      <th key={h} className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {templates.map(t => (
                    <tr key={t.id} className="border-t border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3 font-medium">{t.template_name}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                        {DOC_TEMPLATE_TYPES.find(x => x.value === t.template_type)?.label ?? t.template_type.replace(/_/g, ' ')}
                      </td>
                      <td className="px-4 py-3">
                        {t.is_default ? (
                          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">Default</span>
                        ) : (
                          <button onClick={() => setDefault(t.id)} className="rounded-full border border-gray-300 px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-50">
                            Set Default
                          </button>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                          {t.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{formatDate(t.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          <button onClick={() => setPreviewTarget(t)} className="rounded border border-purple-200 px-2 py-1 text-xs text-purple-600 hover:bg-purple-50">Preview</button>
                          <button onClick={() => openEdit(t)} className="rounded border border-gray-200 px-2 py-1 text-xs hover:bg-gray-50 dark:border-gray-600">Edit</button>
                          <button onClick={() => setBulkPrintTarget(t)} className="rounded border border-blue-200 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50">Bulk Print</button>
                          <button onClick={() => remove(t.id)} className="rounded border border-red-200 px-2 py-1 text-xs text-red-600 hover:bg-red-50">Del</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {bulkPrintTarget && (
            <BulkPrintModal template={bulkPrintTarget} onClose={() => setBulkPrintTarget(null)} />
          )}
          {previewTarget && (
            <TemplatePreviewModal template={previewTarget} onClose={() => setPreviewTarget(null)} />
          )}
        </>
      )}

      {/* ── NOTIFICATION TEMPLATES TAB ────────────────────────────────────── */}
      {tab === 'notification' && (
        <>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setNotifFilterTrigger('')}
                className={`rounded-full px-3 py-1 text-xs font-medium border ${!notifFilterTrigger ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-300 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400'}`}
              >
                All Triggers
              </button>
              {NOTIFICATION_TRIGGERS.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setNotifFilterTrigger(value)}
                  className={`rounded-full px-3 py-1 text-xs font-medium border ${notifFilterTrigger === value ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-300 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400'}`}
                >
                  {label}
                </button>
              ))}
            </div>
            <button onClick={openCreateNotif} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              + New Template
            </button>
          </div>

          {notifLoading ? (
            <p className="py-12 text-center text-gray-500">Loading...</p>
          ) : filteredNotif.length === 0 ? (
            <div className="rounded-xl border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
              <p className="text-gray-500">No notification templates found.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(notifByTrigger).map(([trigger, items]) => {
                const triggerLabel = NOTIFICATION_TRIGGERS.find(x => x.value === trigger)?.label ?? trigger.replace(/_/g, ' ');
                return (
                  <div key={trigger} className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
                    <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-gray-700">
                      <h3 className="font-semibold text-gray-700 dark:text-gray-200 capitalize">{triggerLabel}</h3>
                      <span className="text-xs text-gray-400">{items.length} template{items.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="divide-y divide-gray-100 dark:divide-gray-700">
                      {items.map(t => (
                        <div key={t.id} className={`px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/40 ${t.is_default ? 'bg-green-50/40 dark:bg-green-900/10' : ''}`}>
                          <div className="flex flex-wrap items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-center gap-2 mb-1">
                                <span className="font-medium text-sm">{t.name}</span>
                                {t.is_default && (
                                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">Default</span>
                                )}
                                {!t.is_active && (
                                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">Inactive</span>
                                )}
                              </div>
                              <div className="flex flex-wrap gap-1 mb-1.5">
                                {(t.channels ?? []).map(ch => (
                                  <span key={ch} className={`rounded-full px-2 py-0.5 text-xs font-medium ${CHANNEL_COLORS[ch] ?? 'bg-gray-100 text-gray-600'}`}>
                                    {CHANNEL_LABELS[ch] ?? ch}
                                  </span>
                                ))}
                              </div>
                              {t.subject && (
                                <p className="text-xs text-gray-500 mb-1"><strong>Subject:</strong> {t.subject}</p>
                              )}
                              <p className="text-xs text-gray-500 line-clamp-2 whitespace-pre-wrap">{t.body_template}</p>
                            </div>
                            <div className="flex shrink-0 gap-1">
                              {!t.is_default && (
                                <button onClick={() => setDefaultNotif(t.id)} className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-500 hover:bg-gray-50">
                                  Set Default
                                </button>
                              )}
                              <button onClick={() => openEditNotif(t)} className="rounded border border-gray-200 px-2 py-1 text-xs hover:bg-gray-50">Edit</button>
                              <button onClick={() => removeNotif(t.id)} className="rounded border border-red-200 px-2 py-1 text-xs text-red-600 hover:bg-red-50">Del</button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Notification Template Modal */}
          {showNotifModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
              <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800 max-h-[90vh] overflow-y-auto">
                <h3 className="mb-4 text-lg font-semibold">{editNotifTarget ? 'Edit Notification Template' : 'New Notification Template'}</h3>
                <form onSubmit={saveNotif} className="space-y-3">
                  <div>
                    <label className="mb-1 block text-sm font-medium">Template Name</label>
                    <input type="text" value={notifForm.name} required onChange={e => setNotifForm(p => ({ ...p, name: e.target.value }))}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">Event Trigger</label>
                    <select value={notifForm.event_trigger} onChange={e => setNotifForm(p => ({ ...p, event_trigger: e.target.value }))}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700">
                      {NOTIFICATION_TRIGGERS.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">Channels</label>
                    <div className="flex flex-wrap gap-3">
                      {Object.entries(CHANNEL_LABELS).map(([ch, lbl]) => (
                        <label key={ch} className="flex items-center gap-1.5 cursor-pointer text-sm">
                          <input type="checkbox" checked={notifForm.channels.includes(ch)}
                            onChange={e => setNotifForm(p => ({
                              ...p,
                              channels: e.target.checked ? [...p.channels, ch] : p.channels.filter(c => c !== ch),
                            }))}
                            className="rounded" />
                          {lbl}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">Subject <span className="text-gray-400 font-normal">(email only)</span></label>
                    <input type="text" value={notifForm.subject} onChange={e => setNotifForm(p => ({ ...p, subject: e.target.value }))}
                      placeholder="e.g. Fee Due Reminder – {student_name}"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700" />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">Message Body</label>
                    <textarea value={notifForm.body_template} rows={6} required onChange={e => setNotifForm(p => ({ ...p, body_template: e.target.value }))}
                      placeholder="Use {student_name}, {amount}, {due_date}, {school_name} etc."
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-700" />
                  </div>
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 cursor-pointer text-sm">
                      <input type="checkbox" checked={notifForm.is_active} onChange={e => setNotifForm(p => ({ ...p, is_active: e.target.checked }))} className="rounded" />
                      Active
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-sm">
                      <input type="checkbox" checked={notifForm.is_default} onChange={e => setNotifForm(p => ({ ...p, is_default: e.target.checked }))} className="rounded" />
                      Set as Default
                    </label>
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button type="button" onClick={() => setShowNotifModal(false)} className="rounded-lg border px-4 py-2 text-sm">Cancel</button>
                    <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">Save</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── DOCUMENT template modal ──────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800 max-h-[90vh] overflow-y-auto">
            <h3 className="mb-4 text-lg font-semibold">{editTarget ? 'Edit Template' : 'New Template'}</h3>
            <form onSubmit={save} className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium">Template Name</label>
                <input type="text" value={form.template_name} required
                  onChange={e => setForm(p => ({ ...p, template_name: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Template Type</label>
                <select value={form.template_type}
                  onChange={e => setForm(p => ({ ...p, template_type: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                >
                  {DOC_TEMPLATE_TYPES.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Description</label>
                <input type="text" value={form.description}
                  onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">HTML Content</label>
                <textarea value={form.html_content} rows={8}
                  onChange={e => setForm(p => ({ ...p, html_content: e.target.value }))}
                  placeholder="Enter HTML template with {{variable}} placeholders..."
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono dark:border-gray-600 dark:bg-gray-700"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.is_active}
                  onChange={e => setForm(p => ({ ...p, is_active: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Active</span>
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="rounded-lg border px-4 py-2 text-sm">Cancel</button>
                <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Page;
