import React from 'react';
import EnquiryForm from '@components/public/EnquiryForm';

const SiteEnquiryPage: React.FC = () => (
  <div className="mx-auto max-w-3xl px-4 py-14">
    <h1 className="mb-2 text-3xl font-bold text-gray-900">Enquiry</h1>
    <p className="mb-6 text-sm text-gray-500">
      Have a question? Fill in the form below and our team will get back to you.
    </p>
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <EnquiryForm />
    </div>
  </div>
);

export default SiteEnquiryPage;
