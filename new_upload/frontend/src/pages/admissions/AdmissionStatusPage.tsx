import React from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { admissionsApi } from '@api/admissions';

const unwrap = (res: any) => res?.data ?? res;

const AdmissionStatusPage: React.FC = () => {
  const [reference, setReference] = React.useState('');
  const [result, setResult] = React.useState<any>(null);

  const checkMutation = useMutation({
    mutationFn: () => admissionsApi.checkStatus(reference),
    onSuccess: (res) => setResult(unwrap(res)),
    onError: () => {
      setResult(null);
      toast.error('Reference not found');
    },
  });

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="mx-auto max-w-2xl rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="mb-2 text-2xl font-semibold">Check Admission Status</h1>
        <p className="mb-4 text-sm text-gray-500">Enter your admission reference number</p>

        <div className="flex gap-2">
          <input
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            placeholder="e.g. DEMO-2026-20260303154201"
            className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
          />
          <button
            onClick={() => {
              if (!reference) {
                toast.error('Reference is required');
                return;
              }
              checkMutation.mutate();
            }}
            className="rounded bg-brand-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Check
          </button>
        </div>

        {result && (
          <div className="mt-5 rounded-lg border border-gray-200 p-4">
            <p className="text-sm"><span className="font-semibold">Reference:</span> {result.reference_number}</p>
            <p className="text-sm"><span className="font-semibold">Applicant:</span> {result.applicant_name}</p>
            <p className="text-sm"><span className="font-semibold">Status:</span> {String(result.status)}</p>
            <p className="text-sm"><span className="font-semibold">Submitted:</span> {result.submitted_at ? new Date(result.submitted_at).toLocaleString() : '-'}</p>
            <p className="text-sm"><span className="font-semibold">Remarks:</span> {result.remarks || '-'}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdmissionStatusPage;
