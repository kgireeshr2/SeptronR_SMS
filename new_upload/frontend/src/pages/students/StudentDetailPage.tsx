import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { PageHeader } from '@components/shared/PageHeader';
import { studentsApi, StudentDetail, StudentParent, StudentDocument, StudentEnrollment } from '@api/students';
import { classesApi } from '@api/classes';
import { academicYearsApi } from '@api/academicYears';
import { formatDate } from '@utils/formatters';
import StudentFeeTab from './StudentFeeTab';
import PersonalExpensesTab from './PersonalExpensesTab';
import StudentDuesTab from './StudentDuesTab';
import EditStudentModal from './EditStudentModal';

const unwrap = (r: any) => r?.data ?? r;

const StudentDetailPage: React.FC = () => {
  const { studentId } = useParams<{ studentId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'profile' | 'parents' | 'enrollments' | 'documents' | 'dues' | 'fees' | 'personal-expenses'>('profile');
  const [showEdit, setShowEdit] = useState(false);
  const [showAddDoc, setShowAddDoc] = useState(false);
  const [docForm, setDocForm] = useState({ doc_type: '', file: null as File | null });
  const [docSaving, setDocSaving] = useState(false);
  const [viewDoc, setViewDoc] = useState<{ url: string; name: string } | null>(null);
  const [docZoom, setDocZoom] = useState(100);

  // Fetch student details
  const { data: student, isLoading } = useQuery<StudentDetail>({
    queryKey: ['students', studentId],
    queryFn: async () => {
      if (!studentId) throw new Error('Student ID is required');
      const response = await studentsApi.getStudent(studentId);
      return unwrap(response);
    },
    enabled: !!studentId,
  });

  // Fetch academic years for enrollment name resolution
  const yearsQ = useQuery({
    queryKey: ['academic-years-select'],
    queryFn: async () => {
      const d = unwrap(await academicYearsApi.list());
      return Array.isArray(d) ? d : (d?.items ?? []);
    },
  });
  const years = yearsQ.data ?? [];

  // Collect unique year IDs from this student's enrollments
  const enrollmentYearIds: string[] = useMemo(
    () => [...new Set((student?.enrollments ?? []).map((e: any) => e.academic_year_id).filter(Boolean))],
    [student?.enrollments]
  );

  // Fetch classes for all years used in enrollments (one query per year, combined)
  const allClassesQ = useQuery({
    queryKey: ['classes-all-years', enrollmentYearIds.join(',')],
    enabled: enrollmentYearIds.length > 0,
    queryFn: async () => {
      const results = await Promise.all(
        enrollmentYearIds.map(yid =>
          classesApi.list(yid).then(r => unwrap(r)).then(d => Array.isArray(d) ? d : (d?.items ?? []))
        )
      );
      return results.flat();
    },
  });
  const allClasses: any[] = allClassesQ.data ?? [];

  // Build lookup maps for fast name resolution
  const yearMap = useMemo(() => Object.fromEntries(years.map((y: any) => [y.id, y.name])), [years]);
  const classMap = useMemo(() => Object.fromEntries(allClasses.map((c: any) => [c.id, c.name])), [allClasses]);
  const sectionMap = useMemo(() => {
    const m: Record<string, string> = {};
    for (const cls of allClasses) {
      for (const sec of (cls.sections ?? [])) {
        m[sec.id] = sec.name;
      }
    }
    return m;
  }, [allClasses]);

  // Photo upload mutation
  const uploadPhotoMutation = useMutation({
    mutationFn: ({ studentId, file }: { studentId: string; file: File }) =>
      studentsApi.uploadPhoto(studentId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students', studentId] });
      console.log('Photo uploaded successfully');
    },
    onError: () => {
      console.error('Failed to upload photo');
    },
  });

  // Delete parent mutation
  const deleteParentMutation = useMutation({
    mutationFn: (parentId: string) => studentsApi.deleteParent(parentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students', studentId] });
      console.log('Parent deleted successfully');
    },
    onError: () => {
      console.error('Failed to delete parent');
    },
  });

  // Delete document mutation
  const deleteDocumentMutation = useMutation({
    mutationFn: (documentId: string) => studentsApi.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students', studentId] });
      console.log('Document deleted successfully');
    },
    onError: () => {
      console.error('Failed to delete document');
    },
  });

  const handlePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && studentId) {
      uploadPhotoMutation.mutate({ studentId, file });
    }
  };

  const handleDeleteParent = (parentId: string, parentName: string) => {
    if (window.confirm(`Are you sure you want to delete parent ${parentName}?`)) {
      deleteParentMutation.mutate(parentId);
    }
  };

  const handleDeleteDocument = (documentId: string, docType: string) => {
    if (window.confirm(`Are you sure you want to delete document ${docType}?`)) {
      deleteDocumentMutation.mutate(documentId);
    }
  };

  const handleAddDocument = async () => {
    if (!docForm.doc_type.trim()) return toast.error('Document type is required');
    if (!docForm.file) return toast.error('Please select a file');
    setDocSaving(true);
    try {
      await studentsApi.uploadDocument(studentId!, docForm.doc_type.trim(), docForm.file);
      queryClient.invalidateQueries({ queryKey: ['students', studentId] });
      toast.success('Document uploaded successfully');
      setShowAddDoc(false);
      setDocForm({ doc_type: '', file: null });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to upload document');
    } finally {
      setDocSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Student Details" />
        <div className="p-8 text-center">
          <div className="text-gray-500">Loading student details...</div>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div>
        <PageHeader title="Student Details" />
        <div className="p-8 text-center">
          <div className="text-gray-500">Student not found</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`${student.full_name}`}
        subtitle={`Admission No: ${student.admission_number}`}
        actions={
          <button
            onClick={() => setShowEdit(true)}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 shadow-sm"
          >
            ✏️ Edit Student
          </button>
        }
      />

      {/* Student Header Card */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-start gap-6">
          <div className="relative">
            <div className="h-32 w-32 overflow-hidden rounded-lg bg-gray-200">
              {student.photo_url ? (
                <img src={student.photo_url} alt={student.full_name} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-4xl font-bold text-gray-400">
                  {student.first_name[0]}
                  {student.last_name[0]}
                </div>
              )}
            </div>
            <label
              htmlFor="photo-upload"
              className="absolute bottom-0 right-0 cursor-pointer rounded-full bg-blue-600 p-2 text-white hover:bg-blue-700"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </label>
            <input
              id="photo-upload"
              type="file"
              accept="image/*"
              onChange={handlePhotoUpload}
              className="hidden"
            />
          </div>

          <div className="flex-1 grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-500">Gender</div>
              <div className="mt-1 text-base text-gray-900 dark:text-white">{student.gender}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Date of Birth</div>
              <div className="mt-1 text-base text-gray-900 dark:text-white">
                {formatDate(student.date_of_birth)} ({student.age} years)
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Blood Group</div>
              <div className="mt-1 text-base text-gray-900 dark:text-white">{student.blood_group || 'Not specified'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Religion</div>
              <div className="mt-1 text-base text-gray-900 dark:text-white">{student.religion || 'Not specified'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Category</div>
              <div className="mt-1 text-base text-gray-900 dark:text-white">{student.category || 'Not specified'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Nationality</div>
              <div className="mt-1 text-base text-gray-900 dark:text-white">{student.nationality}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Admission Date</div>
              <div className="mt-1 text-base text-gray-900 dark:text-white">
                {formatDate(student.admission_date)}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500">Status</div>
              <div className="mt-1">
                <span
                  className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
                    student.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}
                >
                  {student.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {(['profile', 'parents', 'enrollments', 'documents', 'dues', 'fees', 'personal-expenses'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`border-b-2 py-4 px-1 text-sm font-medium capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              {tab === 'personal-expenses' ? 'Personal Expenses' : tab === 'dues' ? '💰 Collections' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {activeTab === 'profile' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Profile Information</h3>
              <button onClick={() => setShowEdit(true)} className="text-sm text-blue-600 hover:text-blue-800 font-medium">✏️ Edit</button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium text-gray-500">First Name</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">{student.first_name}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Last Name</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">{student.last_name}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Date of Birth</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">
                  {formatDate(student.date_of_birth)} ({student.age} yrs)
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Gender</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white capitalize">{student.gender}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Admission Date</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">
                  {formatDate(student.admission_date)}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Nationality</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">{student.nationality}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Blood Group</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">{student.blood_group || '—'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Religion</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">{student.religion || '—'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Category</div>
                <div className="mt-1 text-base text-gray-900 dark:text-white">{student.category || '—'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-500">Status</div>
                <div className="mt-1">
                  <span className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
                    student.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>{student.is_active ? 'Active' : 'Inactive'}</span>
                </div>
              </div>
            </div>

            <div className="mt-6 border-t border-gray-100 dark:border-gray-700 pt-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">Government IDs</p>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm font-medium text-gray-500">Aadhaar No.</div>
                  <div className="mt-1 text-base text-gray-900 dark:text-white font-mono">
                    {student.aadhaar_number || '—'}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-500">PAN No.</div>
                  <div className="mt-1 text-base text-gray-900 dark:text-white font-mono">
                    {student.pan_number || '—'}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-500">APAAR / PEN No.</div>
                  <div className="mt-1 text-base text-gray-900 dark:text-white font-mono">
                    {(student as any).apaar_number || '—'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'parents' && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Parents & Guardians</h3>
              <button
                onClick={() => { setShowEdit(true); }}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                ✏️ Edit / Add Parents
              </button>
            </div>
            {student.parents.length === 0 ? (
              <div className="text-center text-gray-500">No parents added yet</div>
            ) : (
              <div className="space-y-4">
                {student.parents.map((parent: StudentParent) => (
                  <div
                    key={parent.id}
                    className="rounded-lg border border-gray-200 p-4 dark:border-gray-700"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                    <div className="font-medium text-gray-900 dark:text-white">{parent.name}</div>
                    <div className="text-sm text-gray-500 capitalize">{parent.relation}</div>
                    {parent.phone && <div className="text-sm text-gray-600">📞 {parent.phone}</div>}
                    {parent.email && <div className="text-sm text-gray-600">✉️ {parent.email}</div>}
                    {parent.occupation && <div className="text-sm text-gray-600">Work: {parent.occupation}</div>}
                    {parent.aadhaar_number && <div className="text-sm text-gray-500 font-mono">Aadhaar: {parent.aadhaar_number}</div>}
                    {parent.pan_number && <div className="text-sm text-gray-500 font-mono">PAN: {parent.pan_number}</div>}
                    <div className="mt-2 flex gap-2">
                          {parent.is_primary_contact && (
                            <span className="inline-flex rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-800">
                              Primary Contact
                            </span>
                          )}
                          {parent.can_access_portal && (
                            <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
                              Portal Access
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteParent(parent.id, parent.name)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'enrollments' && (
          <div>
            <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Enrollment History</h3>
            {student.enrollments.length === 0 ? (
              <div className="text-center text-gray-500">No enrollments found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                        Academic Year
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Class</th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Section</th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                        Roll Number
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {student.enrollments.map((enrollment: StudentEnrollment) => (
                      <tr key={enrollment.id}>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                          {yearMap[enrollment.academic_year_id] ?? enrollment.academic_year_id}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                          {classMap[enrollment.class_id] ?? enrollment.class_id}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                          {enrollment.section_id ? (sectionMap[enrollment.section_id] ? `Section ${sectionMap[enrollment.section_id]}` : enrollment.section_id) : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                          {enrollment.roll_number || 'Not assigned'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span
                            className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                              enrollment.is_current
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {enrollment.is_current ? 'Current' : 'Past'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'dues' && (
          <StudentDuesTab
            studentId={studentId!}
            studentName={student.full_name}
            admissionNumber={student.admission_number}
          />
        )}

        {activeTab === 'fees' && (
          <StudentFeeTab
            studentId={studentId!}
            studentName={student.full_name}
            admissionNumber={student.admission_number}
          />
        )}

        {activeTab === 'personal-expenses' && (
          <PersonalExpensesTab
            studentId={studentId!}
            studentName={student.full_name}
          />
        )}

        {activeTab === 'documents' && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Documents</h3>
              <button
                onClick={() => setShowAddDoc(true)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                + Add Document
              </button>
            </div>
            {student.documents.length === 0 ? (
              <div className="text-center text-gray-500">No documents uploaded yet</div>
            ) : (
              <div className="space-y-2">
                {student.documents.map((doc: StudentDocument) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between rounded-lg border border-gray-200 p-3 dark:border-gray-700"
                  >
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{doc.doc_type}</div>
                      <div className="text-sm text-gray-500">
                        Uploaded on {formatDate(doc.uploaded_at)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => { setDocZoom(100); setViewDoc({ url: doc.file_url, name: doc.doc_type }); }}
                        className="rounded px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 hover:text-blue-800 dark:hover:bg-blue-900/30"
                      >
                        View
                      </button>
                      <a
                        href={doc.file_url}
                        download
                        className="rounded px-2 py-1 text-xs font-medium text-green-600 hover:bg-green-50 hover:text-green-800 dark:hover:bg-green-900/30"
                      >
                        Download
                      </a>
                      <button
                        onClick={() => handleDeleteDocument(doc.id, doc.doc_type)}
                        className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 hover:text-red-800 dark:hover:bg-red-900/30"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {showEdit && student && (
        <EditStudentModal
          student={student}
          onClose={() => setShowEdit(false)}
          onSaved={() => {
            setShowEdit(false);
            queryClient.invalidateQueries({ queryKey: ['students', studentId] });
          }}
        />
      )}

      {/* Document Viewer Modal */}
      {viewDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setViewDoc(null)}>
          <div
            className="flex w-full max-w-4xl flex-col rounded-xl bg-white shadow-2xl dark:bg-gray-900"
            style={{ maxHeight: '90vh' }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
              <span className="font-semibold text-gray-900 dark:text-white truncate mr-4">{viewDoc.name}</span>
              <div className="flex items-center gap-2 shrink-0">
                {/* Zoom controls */}
                <button
                  onClick={() => setDocZoom(z => Math.max(50, z - 10))}
                  className="rounded border border-gray-300 px-2 py-1 text-sm font-bold text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300"
                  title="Zoom out"
                >−</button>
                <span className="w-14 text-center text-sm text-gray-600 dark:text-gray-400">{docZoom}%</span>
                <button
                  onClick={() => setDocZoom(z => Math.min(200, z + 10))}
                  className="rounded border border-gray-300 px-2 py-1 text-sm font-bold text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300"
                  title="Zoom in"
                >+</button>
                <button
                  onClick={() => setDocZoom(100)}
                  className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400"
                  title="Reset zoom"
                >Reset</button>
                {/* Download */}
                <a
                  href={viewDoc.url}
                  download
                  className="rounded bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700"
                >
                  ↓ Download
                </a>
                {/* Open in new tab */}
                <a
                  href={viewDoc.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
                >
                  ↗ New tab
                </a>
                {/* Close */}
                <button
                  onClick={() => setViewDoc(null)}
                  className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700"
                  title="Close"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
            {/* Content */}
            <div className="flex-1 overflow-auto bg-gray-100 dark:bg-gray-800" style={{ minHeight: 0 }}>
              {(() => {
                const url = viewDoc.url;
                const ext = url.split('.').pop()?.toLowerCase() ?? '';
                const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext);
                const isPdf = ext === 'pdf' || url.includes('.pdf');
                if (isImage) {
                  return (
                    <div className="flex items-center justify-center p-4" style={{ minHeight: '60vh' }}>
                      <img
                        src={url}
                        alt={viewDoc.name}
                        style={{ transform: `scale(${docZoom / 100})`, transformOrigin: 'center top', maxWidth: '100%' }}
                        className="rounded shadow"
                      />
                    </div>
                  );
                }
                if (isPdf) {
                  return (
                    <iframe
                      src={`${url}#zoom=${docZoom}`}
                      title={viewDoc.name}
                      className="w-full"
                      style={{ height: '75vh', transform: `scale(${docZoom / 100})`, transformOrigin: 'top left', width: `${(100 * 100) / docZoom}%` }}
                    />
                  );
                }
                // Unknown file type — offer download
                return (
                  <div className="flex flex-col items-center justify-center gap-4 py-16 text-gray-500">
                    <svg className="h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                    <p>Preview not available for this file type</p>
                    <a href={url} download className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">Download to view</a>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      {/* Add Document Modal */}
      {showAddDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white shadow-xl dark:bg-gray-800 p-6">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Upload Document</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Document Type <span className="text-red-500">*</span>
                </label>
                <select
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  value={docForm.doc_type}
                  onChange={e => setDocForm(f => ({ ...f, doc_type: e.target.value }))}
                >
                  <option value="">Select type</option>
                  {['Birth Certificate', 'Transfer Certificate', 'Aadhaar Card', 'Passport', 'Mark Sheet', 'Medical Certificate', 'Address Proof', 'Caste Certificate', 'Income Certificate', 'Photo', 'Other'].map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
                <input
                  className="mt-2 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700"
                  placeholder="Or type a custom document name…"
                  value={docForm.doc_type}
                  onChange={e => setDocForm(f => ({ ...f, doc_type: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  File <span className="text-red-500">*</span>
                </label>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  className="w-full text-sm text-gray-600 dark:text-gray-300 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-600 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white hover:file:bg-blue-700"
                  onChange={e => setDocForm(f => ({ ...f, file: e.target.files?.[0] ?? null }))}
                />
                {docForm.file && (
                  <p className="text-xs text-green-600 mt-1">✓ {docForm.file.name} ({(docForm.file.size / 1024).toFixed(0)} KB)</p>
                )}
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button
                onClick={handleAddDocument}
                disabled={docSaving}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {docSaving ? 'Uploading…' : 'Upload Document'}
              </button>
              <button
                onClick={() => { setShowAddDoc(false); setDocForm({ doc_type: '', file: null }); }}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentDetailPage;
