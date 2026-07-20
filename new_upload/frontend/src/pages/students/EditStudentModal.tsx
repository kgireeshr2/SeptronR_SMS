/**
 * EditStudentModal — full edit panel for a student:
 *   • Profile: all personal fields + govt IDs + status
 *   • Parents: edit / add / remove parents
 *   • Class & Fees: change enrollment + assign fee master
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Save, Plus, Trash2, UserCheck } from 'lucide-react';
import { toast } from 'sonner';
import { studentsApi, StudentDetail, StudentParent } from '@api/students';
import { classesApi } from '@api/classes';
import { academicYearsApi } from '@api/academicYears';
import { feesV2Api } from '@api/feesV2';

const unwrap = (r: any) => r?.data ?? r;

const INPUT = 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white';
const LABEL = 'mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400';

type EditTab = 'profile' | 'parents' | 'class';

interface ParentRow extends Partial<StudentParent> {
  _key: string;       // local unique key
  _isNew?: boolean;   // not yet saved
  _deleted?: boolean; // marked for deletion
  // form fields (always string for form, convert on save)
  relation: string;
  name: string;
  phone: string;
  email: string;
  occupation: string;
  address: string;
  aadhaar_number: string;
  pan_number: string;
  ration_card_number: string;
  is_primary_contact: boolean;
  can_access_portal: boolean;
}

function parentToRow(p: StudentParent, key: string): ParentRow {
  return {
    ...p,
    _key: key,
    relation: p.relation,
    name: p.name ?? '',
    phone: p.phone ?? '',
    email: p.email ?? '',
    occupation: p.occupation ?? '',
    address: p.address ?? '',
    aadhaar_number: p.aadhaar_number ?? '',
    pan_number: p.pan_number ?? '',
    ration_card_number: p.ration_card_number ?? '',
    is_primary_contact: p.is_primary_contact ?? false,
    can_access_portal: p.can_access_portal ?? true,
  };
}

function emptyParentRow(): ParentRow {
  return {
    _key: `new-${Date.now()}`,
    _isNew: true,
    relation: 'father',
    name: '',
    phone: '',
    email: '',
    occupation: '',
    address: '',
    aadhaar_number: '',
    pan_number: '',
    ration_card_number: '',
    is_primary_contact: false,
    can_access_portal: true,
  };
}

interface Props {
  student: StudentDetail;
  onClose: () => void;
  onSaved: () => void;
}

const EditStudentModal: React.FC<Props> = ({ student, onClose, onSaved }) => {
  const qc = useQueryClient();
  const [tab, setTab] = useState<EditTab>('profile');
  const [saving, setSaving] = useState(false);

  // ── Profile form ───────────────────────────────────────────────────────────
  const [pf, setPf] = useState({
    first_name: student.first_name,
    last_name: student.last_name,
    date_of_birth: student.date_of_birth,
    gender: student.gender,
    admission_date: student.admission_date,
    admission_number: student.admission_number,
    nationality: student.nationality ?? 'Indian',
    blood_group: student.blood_group ?? '',
    religion: student.religion ?? '',
    category: student.category ?? '',
    caste: student.caste ?? '',
    mother_tongue: student.mother_tongue ?? '',
    is_active: student.is_active,
    photo_url: student.photo_url ?? '',
    aadhaar_number: student.aadhaar_number ?? '',
    pan_number: student.pan_number ?? '',
    apaar_number: student.apaar_number ?? '',
    // Contact & Address
    phone: student.phone ?? '',
    email: student.email ?? '',
    address: student.address ?? '',
    city: student.city ?? '',
    state: student.state ?? '',
    pincode: student.pincode ?? '',
    // Additional
    previous_school: student.previous_school ?? '',
    // Emergency Contact
    emergency_contact_name: student.emergency_contact_name ?? '',
    emergency_contact_phone: student.emergency_contact_phone ?? '',
    emergency_contact_relation: student.emergency_contact_relation ?? '',
  });

  const setP = (k: keyof typeof pf, v: any) => setPf(p => ({ ...p, [k]: v }));

  // ── Parents form ───────────────────────────────────────────────────────────
  const [parents, setParents] = useState<ParentRow[]>(() =>
    student.parents.map((p, i) => parentToRow(p, `existing-${i}`))
  );

  const addParentRow = () => setParents(ps => [...ps, emptyParentRow()]);

  const updateParentRow = (key: string, field: keyof ParentRow, value: any) =>
    setParents(ps => ps.map(p => p._key === key ? { ...p, [field]: value } : p));

  const markDelete = (key: string) =>
    setParents(ps => ps.map(p =>
      p._key === key ? { ...p, _deleted: !p._isNew && true } : p
    ).filter(p => !(p._key === key && p._isNew)));

  // ── Class & Fees form ──────────────────────────────────────────────────────
  const currentEnrollment = student.enrollments.find(e => e.is_current);
  const [enrollment, setEnrollment] = useState({
    academic_year_id: currentEnrollment?.academic_year_id ?? '',
    class_id: currentEnrollment?.class_id ?? '',
    section_id: currentEnrollment?.section_id ?? '',
    roll_number: currentEnrollment?.roll_number ?? '',
    fee_master_id: '',
  });
  const setE = (k: keyof typeof enrollment, v: string) => setEnrollment(e => ({ ...e, [k]: v }));

  // Queries for Class & Fees tab
  const yearsQ = useQuery({
    queryKey: ['academic-years-select'],
    queryFn: async () => {
      const d = unwrap(await academicYearsApi.list());
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });
  const years = yearsQ.data ?? [];

  const classesQ = useQuery({
    queryKey: ['classes-for-enroll', enrollment.academic_year_id],
    enabled: !!enrollment.academic_year_id,
    queryFn: async () => {
      const d = unwrap(await classesApi.list(enrollment.academic_year_id));
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });
  const classes = classesQ.data ?? [];

  const sections = useMemo(() => {
    if (!enrollment.class_id) return [];
    const cls = classes.find((c: any) => c.id === enrollment.class_id);
    return (cls as any)?.sections ?? [];
  }, [enrollment.class_id, classes]);

  const feeMastersQ = useQuery({
    queryKey: ['fee-masters-for-edit', enrollment.class_id, enrollment.academic_year_id],
    enabled: !!enrollment.class_id,
    queryFn: async () => {
      const d = unwrap(await feesV2Api.listFeeMasters(
        enrollment.academic_year_id
          ? { class_id: enrollment.class_id, academic_year_id: enrollment.academic_year_id }
          : { class_id: enrollment.class_id }
      ));
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });
  const feeMasters = feeMastersQ.data ?? [];

  // ── Aadhaar validation helper ──────────────────────────────────────────────
  const handleAadhaar = (val: string) =>
    val.replace(/\D/g, '').slice(0, 12);

  // ── Save profile ───────────────────────────────────────────────────────────
  const saveProfile = async () => {
    if (!pf.first_name.trim()) return toast.error('First name required');
    if (!pf.last_name.trim()) return toast.error('Last name required');
    if (pf.aadhaar_number && pf.aadhaar_number.length !== 12)
      return toast.error('Aadhaar must be exactly 12 digits');
    await studentsApi.updateStudent(student.id, {
      first_name: pf.first_name.trim(),
      last_name: pf.last_name.trim(),
      date_of_birth: pf.date_of_birth,
      gender: pf.gender,
      admission_date: pf.admission_date,
      admission_number: pf.admission_number || undefined,
      nationality: pf.nationality || 'Indian',
      blood_group: pf.blood_group || undefined,
      religion: pf.religion || undefined,
      category: pf.category || undefined,
      caste: pf.caste || undefined,
      mother_tongue: pf.mother_tongue || undefined,
      is_active: pf.is_active,
      photo_url: pf.photo_url || undefined,
      aadhaar_number: pf.aadhaar_number || undefined,
      pan_number: pf.pan_number || undefined,
      apaar_number: pf.apaar_number || undefined,
      // Contact & Address
      phone: pf.phone || undefined,
      email: pf.email || undefined,
      address: pf.address || undefined,
      city: pf.city || undefined,
      state: pf.state || undefined,
      pincode: pf.pincode || undefined,
      // Additional
      previous_school: pf.previous_school || undefined,
      // Emergency Contact
      emergency_contact_name: pf.emergency_contact_name || undefined,
      emergency_contact_phone: pf.emergency_contact_phone || undefined,
      emergency_contact_relation: pf.emergency_contact_relation || undefined,
    });
  };

  // ── Save parents ───────────────────────────────────────────────────────────
  const saveParents = async () => {
    for (const row of parents) {
      if (row._deleted && row.id) {
        await studentsApi.deleteParent(row.id);
      } else if (row._isNew && !row._deleted && row.name.trim()) {
        await studentsApi.addParent(student.id, {
          relation: row.relation,
          name: row.name.trim(),
          phone: row.phone || undefined,
          email: row.email || undefined,
          occupation: row.occupation || undefined,
          address: row.address || undefined,
          is_primary_contact: row.is_primary_contact,
          can_access_portal: row.can_access_portal,
          aadhaar_number: row.aadhaar_number || undefined,
          pan_number: row.pan_number || undefined,
          ration_card_number: row.ration_card_number || undefined,
        });
      } else if (!row._isNew && !row._deleted && row.id) {
        await studentsApi.updateParent(row.id, {
          relation: row.relation as any,
          name: row.name.trim(),
          phone: row.phone || undefined,
          email: row.email || undefined,
          occupation: row.occupation || undefined,
          address: row.address || undefined,
          is_primary_contact: row.is_primary_contact,
          can_access_portal: row.can_access_portal,
          aadhaar_number: row.aadhaar_number || undefined,
          pan_number: row.pan_number || undefined,
          ration_card_number: row.ration_card_number || undefined,
        });
      }
    }
  };

  // ── Save enrollment ────────────────────────────────────────────────────────
  const saveEnrollment = async () => {
    // Only create new enrollment if class changed
    const changed =
      enrollment.class_id !== currentEnrollment?.class_id ||
      enrollment.section_id !== currentEnrollment?.section_id ||
      enrollment.academic_year_id !== currentEnrollment?.academic_year_id;

    if (changed && enrollment.class_id) {
      await studentsApi.addEnrollment(student.id, {
        academic_year_id: enrollment.academic_year_id,
        class_id: enrollment.class_id,
        section_id: enrollment.section_id,
        roll_number: enrollment.roll_number || undefined,
        is_current: true,
      });
    }
    if (enrollment.fee_master_id && enrollment.academic_year_id) {
      await feesV2Api.assignFeeMaster({
        student_ids: [student.id],
        fee_master_id: enrollment.fee_master_id,
        academic_year_id: enrollment.academic_year_id,
      });
    }
  };

  // ── Master Save handler ────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true);
    try {
      await saveProfile();
      await saveParents();
      await saveEnrollment();
      await qc.invalidateQueries({ queryKey: ['students', student.id] });
      toast.success('Student updated successfully');
      onSaved();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.message ?? 'Failed to save';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  };

  const TABS: { key: EditTab; label: string }[] = [
    { key: 'profile', label: '👤 Profile' },
    { key: 'parents', label: `👨‍👩‍👧 Parents (${parents.filter(p => !p._deleted).length})` },
    { key: 'class', label: '🏫 Class & Fees' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-10">
      <div className="w-full max-w-3xl rounded-2xl bg-white shadow-2xl dark:bg-gray-900 mb-10">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">
              Edit Student — {student.full_name}
            </h2>
            <p className="text-xs text-gray-500">{student.admission_number}</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700">
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700 px-6">
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>{t.label}</button>
          ))}
        </div>

        <div className="p-6 space-y-5 max-h-[72vh] overflow-y-auto">

          {/* ── PROFILE TAB ── */}
          {tab === 'profile' && (
            <div className="space-y-5">
              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Basic Information</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={LABEL}>First Name <span className="text-red-500">*</span></label>
                    <input className={INPUT} value={pf.first_name} onChange={e => setP('first_name', e.target.value)} />
                  </div>
                  <div>
                    <label className={LABEL}>Last Name <span className="text-red-500">*</span></label>
                    <input className={INPUT} value={pf.last_name} onChange={e => setP('last_name', e.target.value)} />
                  </div>
                  <div>
                    <label className={LABEL}>Date of Birth <span className="text-red-500">*</span></label>
                    <input type="date" className={INPUT} value={pf.date_of_birth} onChange={e => setP('date_of_birth', e.target.value)} />
                  </div>
                  <div>
                    <label className={LABEL}>Gender <span className="text-red-500">*</span></label>
                    <select className={INPUT} value={pf.gender} onChange={e => setP('gender', e.target.value)}>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className={LABEL}>Admission Date</label>
                    <input type="date" className={INPUT} value={pf.admission_date} onChange={e => setP('admission_date', e.target.value)} />
                  </div>
                  <div>
                    <label className={LABEL}>Admission Number</label>
                    <input className={INPUT} value={pf.admission_number} onChange={e => setP('admission_number', e.target.value)} />
                  </div>
                  <div>
                    <label className={LABEL}>Nationality</label>
                    <input className={INPUT} value={pf.nationality} onChange={e => setP('nationality', e.target.value)} placeholder="Indian" />
                  </div>
                  <div>
                    <label className={LABEL}>Status</label>
                    <select className={INPUT} value={pf.is_active ? 'active' : 'inactive'} onChange={e => setP('is_active', e.target.value === 'active')}>
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>
              </section>

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Additional Details</p>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={LABEL}>Blood Group</label>
                    <select className={INPUT} value={pf.blood_group} onChange={e => setP('blood_group', e.target.value)}>
                      <option value="">Select</option>
                      {['A+','A-','B+','B-','AB+','AB-','O+','O-'].map(bg => <option key={bg} value={bg}>{bg}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={LABEL}>Religion</label>
                    <input className={INPUT} value={pf.religion} onChange={e => setP('religion', e.target.value)} placeholder="e.g. Hindu, Muslim..." />
                  </div>
                  <div>
                    <label className={LABEL}>Category</label>
                    <select className={INPUT} value={pf.category} onChange={e => setP('category', e.target.value)}>
                      <option value="">Select</option>
                      {['General','OBC','SC','ST','EWS','Other'].map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>
              </section>

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Government IDs</p>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={LABEL}>Aadhaar No. <span className="text-gray-400 font-normal">(12 digits)</span></label>
                    <input
                      className={INPUT + ' font-mono tracking-widest'}
                      value={pf.aadhaar_number}
                      inputMode="numeric"
                      onChange={e => setP('aadhaar_number', handleAadhaar(e.target.value))}
                      placeholder="123456789012"
                      maxLength={12}
                    />
                    {pf.aadhaar_number && pf.aadhaar_number.length !== 12 && (
                      <p className="text-xs text-amber-600 mt-0.5">{pf.aadhaar_number.length}/12 digits</p>
                    )}
                    {pf.aadhaar_number.length === 12 && (
                      <p className="text-xs text-green-600 mt-0.5">✓ Valid length</p>
                    )}
                  </div>
                  <div>
                    <label className={LABEL}>PAN No.</label>
                    <input
                      className={INPUT + ' font-mono uppercase'}
                      value={pf.pan_number}
                      onChange={e => setP('pan_number', e.target.value.toUpperCase())}
                      placeholder="ABCDE1234F"
                      maxLength={10}
                    />
                  </div>
                  <div>
                    <label className={LABEL}>APAAR / PEN No.</label>
                    <input
                      className={INPUT}
                      value={pf.apaar_number}
                      onChange={e => setP('apaar_number', e.target.value)}
                      placeholder="APAAR / PEN number"
                    />
                  </div>
                </div>
              </section>

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Contact & Address</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={LABEL}>Phone</label>
                    <input type="tel" className={INPUT} value={pf.phone} onChange={e => setP('phone', e.target.value)} placeholder="+91 98765 43210" />
                  </div>
                  <div>
                    <label className={LABEL}>Email</label>
                    <input type="email" className={INPUT} value={pf.email} onChange={e => setP('email', e.target.value)} placeholder="student@email.com" />
                  </div>
                </div>
                <div className="mt-3">
                  <label className={LABEL}>Address</label>
                  <textarea className={INPUT + ' resize-none'} rows={2} value={pf.address} onChange={e => setP('address', e.target.value)} placeholder="House No., Street, Area..." />
                </div>
                <div className="grid grid-cols-3 gap-3 mt-3">
                  <div>
                    <label className={LABEL}>City</label>
                    <input className={INPUT} value={pf.city} onChange={e => setP('city', e.target.value)} placeholder="City" />
                  </div>
                  <div>
                    <label className={LABEL}>State</label>
                    <input className={INPUT} value={pf.state} onChange={e => setP('state', e.target.value)} placeholder="State" />
                  </div>
                  <div>
                    <label className={LABEL}>Pincode</label>
                    <input className={INPUT} value={pf.pincode} onChange={e => setP('pincode', e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="000000" maxLength={6} inputMode="numeric" />
                  </div>
                </div>
              </section>

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Academic Background</p>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={LABEL}>Previous School</label>
                    <input className={INPUT} value={pf.previous_school} onChange={e => setP('previous_school', e.target.value)} placeholder="Previous school name" />
                  </div>
                  <div>
                    <label className={LABEL}>Mother Tongue</label>
                    <input className={INPUT} value={pf.mother_tongue} onChange={e => setP('mother_tongue', e.target.value)} placeholder="e.g. Hindi, Tamil..." />
                  </div>
                  <div>
                    <label className={LABEL}>Caste</label>
                    <input className={INPUT} value={pf.caste} onChange={e => setP('caste', e.target.value)} placeholder="Caste (if applicable)" />
                  </div>
                </div>
              </section>

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Emergency Contact</p>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className={LABEL}>Contact Name</label>
                    <input className={INPUT} value={pf.emergency_contact_name} onChange={e => setP('emergency_contact_name', e.target.value)} placeholder="Emergency contact name" />
                  </div>
                  <div>
                    <label className={LABEL}>Contact Phone</label>
                    <input type="tel" className={INPUT} value={pf.emergency_contact_phone} onChange={e => setP('emergency_contact_phone', e.target.value)} placeholder="+91 98765 43210" />
                  </div>
                  <div>
                    <label className={LABEL}>Relation</label>
                    <select className={INPUT} value={pf.emergency_contact_relation} onChange={e => setP('emergency_contact_relation', e.target.value)}>
                      <option value="">Select</option>
                      {['Father','Mother','Guardian','Sibling','Grandparent','Uncle','Aunt','Other'].map(r => (
                        <option key={r} value={r.toLowerCase()}>{r}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </section>

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Photo</p>
                <div>
                  <label className={LABEL}>Photo URL</label>
                  <input className={INPUT} value={pf.photo_url} onChange={e => setP('photo_url', e.target.value)} placeholder="https://..." />
                  {pf.photo_url && (
                    <img src={pf.photo_url} alt="Preview" className="mt-2 h-16 w-16 rounded-full object-cover border border-gray-200" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                  )}
                </div>
              </section>
            </div>
          )}

          {/* ── PARENTS TAB ── */}
          {tab === 'parents' && (
            <div className="space-y-4">
              {parents.filter(p => !p._deleted).map((row) => (
                <div key={row._key} className="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <select
                        className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium dark:border-gray-600 dark:bg-gray-800"
                        value={row.relation}
                        onChange={e => updateParentRow(row._key, 'relation', e.target.value)}
                      >
                        {['father','mother','guardian','sibling','other'].map(r => (
                          <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                        ))}
                      </select>
                      {row._isNew && <span className="text-xs bg-blue-100 text-blue-700 rounded-full px-2 py-0.5">New</span>}
                    </div>
                    <button onClick={() => markDelete(row._key)} className="text-red-500 hover:text-red-700 p-1">
                      <Trash2 size={15} />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2 md:col-span-1">
                      <label className={LABEL}>Name <span className="text-red-500">*</span></label>
                      <input className={INPUT} value={row.name}
                        onChange={e => updateParentRow(row._key, 'name', e.target.value)}
                        placeholder="Full name" />
                    </div>
                    <div>
                      <label className={LABEL}>Phone</label>
                      <input type="tel" className={INPUT} value={row.phone}
                        onChange={e => updateParentRow(row._key, 'phone', e.target.value)}
                        placeholder="+91 98765 43210" />
                    </div>
                    <div>
                      <label className={LABEL}>Email</label>
                      <input type="email" className={INPUT} value={row.email}
                        onChange={e => updateParentRow(row._key, 'email', e.target.value)}
                        placeholder="email@example.com" />
                    </div>
                    <div>
                      <label className={LABEL}>Occupation</label>
                      <input className={INPUT} value={row.occupation}
                        onChange={e => updateParentRow(row._key, 'occupation', e.target.value)}
                        placeholder="e.g. Engineer" />
                    </div>
                    <div className="col-span-2">
                      <label className={LABEL}>Address</label>
                      <input className={INPUT} value={row.address}
                        onChange={e => updateParentRow(row._key, 'address', e.target.value)}
                        placeholder="Residential address" />
                    </div>
                  </div>

                  <div className="mt-3 grid grid-cols-3 gap-3">
                    <div>
                      <label className={LABEL}>Aadhaar No. <span className="text-gray-400">(12 digits)</span></label>
                      <input className={INPUT + ' font-mono'} value={row.aadhaar_number}
                        inputMode="numeric"
                        onChange={e => updateParentRow(row._key, 'aadhaar_number', e.target.value.replace(/\D/g, '').slice(0, 12))}
                        placeholder="123456789012" maxLength={12} />
                    </div>
                    <div>
                      <label className={LABEL}>PAN No.</label>
                      <input className={INPUT + ' font-mono uppercase'} value={row.pan_number}
                        onChange={e => updateParentRow(row._key, 'pan_number', e.target.value.toUpperCase())}
                        placeholder="ABCDE1234F" maxLength={10} />
                    </div>
                    <div>
                      <label className={LABEL}>Ration Card No.</label>
                      <input className={INPUT} value={row.ration_card_number}
                        onChange={e => updateParentRow(row._key, 'ration_card_number', e.target.value)}
                        placeholder="Ration card number" />
                    </div>
                  </div>

                  <div className="mt-3 flex items-center gap-6">
                    <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-600 dark:text-gray-400">
                      <input type="checkbox" checked={row.is_primary_contact}
                        onChange={e => updateParentRow(row._key, 'is_primary_contact', e.target.checked)}
                        className="h-4 w-4 rounded" />
                      Primary contact
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-600 dark:text-gray-400">
                      <input type="checkbox" checked={row.can_access_portal}
                        onChange={e => updateParentRow(row._key, 'can_access_portal', e.target.checked)}
                        className="h-4 w-4 rounded" />
                      Portal access
                    </label>
                  </div>
                </div>
              ))}

              {parents.filter(p => !p._deleted).length === 0 && (
                <div className="text-center py-8 text-gray-400 border border-dashed border-gray-200 dark:border-gray-700 rounded-xl">
                  <p className="text-sm">No parents added. Click below to add one.</p>
                </div>
              )}

              <button
                onClick={addParentRow}
                className="flex items-center gap-2 px-4 py-2 text-sm border border-dashed border-blue-400 text-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 w-full justify-center"
              >
                <Plus size={15} /> Add Parent / Guardian
              </button>
            </div>
          )}

          {/* ── CLASS & FEES TAB ── */}
          {tab === 'class' && (
            <div className="space-y-5">
              {currentEnrollment && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 text-sm">
                  <p className="font-medium text-blue-700 dark:text-blue-300 mb-1">Current Enrollment</p>
                  <p className="text-blue-600 dark:text-blue-400">
                    Class: {currentEnrollment.class_id} · Section: {currentEnrollment.section_id}
                    {currentEnrollment.roll_number ? ` · Roll: ${currentEnrollment.roll_number}` : ''}
                  </p>
                  <p className="text-xs text-blue-400 mt-1">Changing class will create a new enrollment entry (current one remains in history).</p>
                </div>
              )}

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Change Class / Section</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={LABEL}>Academic Year</label>
                    <select className={INPUT} value={enrollment.academic_year_id}
                      onChange={e => { setE('academic_year_id', e.target.value); setE('class_id', ''); setE('section_id', ''); }}>
                      <option value="">Select year</option>
                      {years.map((y: any) => <option key={y.id} value={y.id}>{y.name}{y.is_current ? ' (✓ Active)' : ''}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={LABEL}>Class</label>
                    <select className={INPUT} value={enrollment.class_id}
                      onChange={e => { setE('class_id', e.target.value); setE('section_id', ''); }}>
                      <option value="">Select class</option>
                      {classes.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={LABEL}>Section</label>
                    <select className={INPUT} value={enrollment.section_id} disabled={!enrollment.class_id}
                      onChange={e => setE('section_id', e.target.value)}>
                      <option value="">Select section</option>
                      {sections.map((s: any) => <option key={s.id} value={s.id}>Section {s.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className={LABEL}>Roll Number</label>
                    <input className={INPUT} value={enrollment.roll_number}
                      onChange={e => setE('roll_number', e.target.value)} placeholder="Optional" />
                  </div>
                </div>
              </section>

              <section>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Assign / Change Fee Master</p>
                <select className={INPUT} value={enrollment.fee_master_id}
                  disabled={!enrollment.class_id}
                  onChange={e => setE('fee_master_id', e.target.value)}>
                  <option value="">No change (keep existing)</option>
                  {feeMasters.map((fm: any) => <option key={fm.id} value={fm.id}>{fm.name}</option>)}
                </select>
                <p className="text-xs text-gray-400 mt-1">Selecting a fee master will create a new fee assignment for this student.</p>
              </section>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 dark:border-gray-700">
          <button onClick={onClose} className="rounded-lg border border-gray-300 px-5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            <Save size={15} /> {saving ? 'Saving…' : 'Save All Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditStudentModal;
