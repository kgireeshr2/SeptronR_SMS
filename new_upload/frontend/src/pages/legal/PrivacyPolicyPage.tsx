import React from 'react';

const PrivacyPolicyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm p-8 md:p-12">
        {/* Header */}
        <div className="mb-8 border-b pb-6">
          <h1 className="text-3xl font-bold text-gray-900">Privacy Policy</h1>
          <p className="mt-2 text-sm text-gray-500">Last updated: April 29, 2026</p>
        </div>

        <div className="prose prose-gray max-w-none space-y-6 text-gray-700 leading-relaxed">

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">1. Introduction</h2>
            <p>
              This Privacy Policy describes how <strong>SeptroSchool</strong> ("we", "our", or "us")
              collects, uses, and shares information when you use our services, including our WhatsApp Business
              messaging integration operated via the Meta Business Platform.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">2. Information We Collect</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Contact information:</strong> Name, phone number, email address provided during registration or admission.</li>
              <li><strong>WhatsApp messages:</strong> Messages exchanged through our WhatsApp Business integration (attendance alerts, fee reminders, notifications).</li>
              <li><strong>Usage data:</strong> Interaction logs, timestamps, and message delivery statuses.</li>
              <li><strong>Device & technical data:</strong> IP address, browser type, and operating system for security and analytics.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">3. How We Use Your Information</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Send school notifications, attendance alerts, fee reminders, and exam results via WhatsApp.</li>
              <li>Operate and improve the SeptroSchool platform.</li>
              <li>Respond to your queries and provide customer support.</li>
              <li>Comply with legal obligations and protect against fraud.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">4. WhatsApp Messaging</h2>
            <p>
              We use the <strong>Meta WhatsApp Business Platform (Cloud API)</strong> to send automated messages.
              By providing your WhatsApp number and opting in, you consent to receive school-related messages.
              Message frequency varies. Standard messaging rates from your carrier may apply.
              You can opt out at any time by replying <strong>STOP</strong> or contacting school administration.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">5. Data Sharing</h2>
            <p>We do not sell your personal data. We may share information with:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Meta Platforms, Inc.</strong> — to deliver WhatsApp messages through the Cloud API.</li>
              <li><strong>Service providers</strong> — hosting, database, and email providers under strict data processing agreements.</li>
              <li><strong>Legal authorities</strong> — when required by applicable law.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">6. Data Retention</h2>
            <p>
              We retain personal data for as long as your account is active or as needed to provide services.
              Message logs are retained for up to 12 months. You may request deletion of your data by contacting us.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">7. Security</h2>
            <p>
              We implement industry-standard security measures including HTTPS encryption, access controls, and
              secure database storage. No method of transmission is 100% secure; we strive to protect your data
              but cannot guarantee absolute security.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">8. Your Rights</h2>
            <p>You have the right to:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Access the personal data we hold about you.</li>
              <li>Request correction of inaccurate data.</li>
              <li>Request deletion of your data (subject to legal obligations).</li>
              <li>Withdraw consent for WhatsApp messaging at any time.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">9. Children's Privacy</h2>
            <p>
              Our platform is operated by schools for managing student records. Student data is managed by
              school administrators on behalf of parents/guardians. We do not knowingly collect data directly
              from children under 13 without parental consent.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">10. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. Changes will be posted on this page
              with the updated date. Continued use of the service after changes constitutes acceptance.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">11. Contact Us</h2>
            <p>For privacy-related questions or to exercise your rights, contact us at:</p>
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

export default PrivacyPolicyPage;
