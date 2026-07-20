import React from 'react';

const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm p-8 md:p-12">
        {/* Header */}
        <div className="mb-8 border-b pb-6">
          <h1 className="text-3xl font-bold text-gray-900">Terms and Conditions</h1>
          <p className="mt-2 text-sm text-gray-500">Last updated: April 29, 2026</p>
        </div>

        <div className="prose prose-gray max-w-none space-y-6 text-gray-700 leading-relaxed">

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">1. Acceptance of Terms</h2>
            <p>
              By accessing or using the <strong>SeptroSchool</strong> platform and its
              WhatsApp Business messaging services, you agree to be bound by these Terms and Conditions.
              If you do not agree, please discontinue use of our services.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">2. Description of Service</h2>
            <p>
              SeptroSchool provides school management tools including student records, attendance tracking, fee management,
              exam management, and communication services via WhatsApp Business (Meta Cloud API).
              The WhatsApp integration allows schools to send automated notifications to parents, students, and staff.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">3. WhatsApp Messaging Terms</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Messages are sent via the <strong>Meta WhatsApp Business Platform</strong>.</li>
              <li>By providing your phone number, you consent to receive school-related WhatsApp messages.</li>
              <li>Message types include: attendance alerts, fee reminders, exam results, and announcements.</li>
              <li>You may opt out at any time by replying <strong>STOP</strong> or contacting school administration.</li>
              <li>Standard carrier messaging and data rates may apply.</li>
              <li>We do not use WhatsApp for marketing or promotional purposes unrelated to school operations.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">4. User Accounts & Access</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Access to the platform is granted by school administrators only.</li>
              <li>You are responsible for maintaining the confidentiality of your login credentials.</li>
              <li>You must notify the administrator immediately if you suspect unauthorized access.</li>
              <li>We reserve the right to suspend accounts that violate these terms.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">5. Acceptable Use</h2>
            <p>You agree not to:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Use the platform for any unlawful purpose.</li>
              <li>Share login credentials with unauthorized persons.</li>
              <li>Attempt to access data of other schools or users.</li>
              <li>Misuse the WhatsApp messaging feature to send spam or unsolicited messages.</li>
              <li>Reverse engineer or tamper with the platform.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">6. Data Ownership</h2>
            <p>
              All student and school data entered into the system remains the property of the respective school.
              We act as a data processor and do not claim ownership of your data.
              You grant us a limited license to process your data solely to provide the services.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">7. Availability & Downtime</h2>
            <p>
              We strive to maintain 99% uptime but do not guarantee uninterrupted availability.
              Scheduled maintenance will be communicated in advance where possible.
              We are not liable for losses arising from service downtime or interruption.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">8. Limitation of Liability</h2>
            <p>
              To the fullest extent permitted by law, SeptroSchool shall not be liable for any indirect, incidental,
              special, or consequential damages arising from the use or inability to use the service,
              including any loss of data or unauthorized access to your account.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">9. Third-Party Services</h2>
            <p>
              Our platform integrates with third-party services including Meta (WhatsApp), cloud hosting providers,
              and email services. Your use of these integrations is also subject to the respective third-party terms:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              <li><a href="https://www.whatsapp.com/legal/terms-of-service" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">WhatsApp Terms of Service</a></li>
              <li><a href="https://developers.facebook.com/terms/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Meta Platform Terms</a></li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">10. Modifications</h2>
            <p>
              We reserve the right to modify these Terms at any time. Changes take effect upon posting.
              Continued use of the service constitutes acceptance of the updated Terms.
              We will notify school administrators of material changes via email or system notification.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">11. Governing Law</h2>
            <p>
              These Terms are governed by the laws of India. Any disputes shall be subject to the
              exclusive jurisdiction of the courts in India.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">12. Contact Us</h2>
            <p>For questions about these Terms, contact us at:</p>
            <div className="mt-2 bg-gray-50 rounded-lg p-4 text-sm">
              <p><strong>SeptroSchool</strong></p>
              <p>Email: <a href="mailto:support@septronr.com" className="text-blue-600 hover:underline">support@septronr.com</a></p>
              <p>Website: <a href="https://smsapi.septronr.com" className="text-blue-600 hover:underline">smsapi.septronr.com</a></p>
            </div>
          </section>
        </div>

        <div className="mt-10 pt-6 border-t text-center text-sm text-gray-400">
          © {new Date().getFullYear()} SeptroSchool. All rights reserved.
        </div>
      </div>
    </div>
  );
};

export default TermsPage;
