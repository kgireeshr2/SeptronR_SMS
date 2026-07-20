import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { PrivateRoute } from './PrivateRoute';

// ── Lazy-loaded page components (stubs created for each module) ───────────────
const LoginPage = lazy(() => import('@pages/auth/LoginPage'));
const ForgotPasswordPage = lazy(() => import('@pages/auth/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('@pages/auth/ResetPasswordPage'));

const AppLayout = lazy(() => import('@components/layout/AppLayout'));
const SuperAdminLayout = lazy(() => import('@components/layout/SuperAdminLayout'));

const Dashboard = lazy(() => import('@pages/dashboard/DashboardPage'));
const SuperAdminPage = lazy(() => import('@pages/superadmin/SuperAdminPage'));

// Academic
const AcademicYearsPage = lazy(() => import('@pages/academic/AcademicYearsPage'));
const AdmissionsPage = lazy(() => import('@pages/admissions/AdmissionsPage'));
const PublicAdmissionApplyPage = lazy(() => import('@pages/admissions/PublicAdmissionApplyPage'));
const AdmissionStatusPage = lazy(() => import('@pages/admissions/AdmissionStatusPage'));

// Classes
const ClassesPage = lazy(() => import('@pages/classes/ClassesPage'));
const SubjectsPage = lazy(() => import('@pages/classes/SubjectsPage'));
const TimetablePage = lazy(() => import('@pages/classes/TimetablePage'));

// People
const StudentsPage = lazy(() => import('@pages/students/StudentsPage'));
const StudentDetailPage = lazy(() => import('@pages/students/StudentDetailPage'));
const StaffPage = lazy(() => import('@pages/staff/StaffPage'));
const StaffFormPage = lazy(() => import('@pages/staff/StaffFormPage'));
const StaffDetailPage = lazy(() => import('@pages/staff/StaffDetailPage'));
const DepartmentsPage = lazy(() => import('@pages/staff/DepartmentsPage'));
const PayrollPage = lazy(() => import('@pages/payroll/PayrollPage'));
const LeavesPage = lazy(() => import('@pages/leaves/LeavesPage'));

// Operations
const AttendancePage = lazy(() => import('@pages/attendance/AttendancePage'));
const FeesPage = lazy(() => import('@pages/fees/FeesPage'));
const AdvancedFeesPage = lazy(() => import('@pages/fees/AdvancedFeesPage'));
const PersonalExpensesPage = lazy(() => import('@pages/fees/PersonalExpensesPage'));
const ExamsPage = lazy(() => import('@pages/exams/ExamsPage'));
const LibraryPage = lazy(() => import('@pages/library/LibraryPage'));
const TransportPage = lazy(() => import('@pages/transport/TransportPage'));
const InventoryPage = lazy(() => import('@pages/inventory/InventoryPage'));
const AccountingPage = lazy(() => import('@pages/accounting/AccountingPage'));
const VendorInventoryPage = lazy(() => import('@pages/vendor-inventory/VendorInventoryPage'));

// Communication
const CommunicationPage = lazy(() => import('@pages/communication/CommunicationPage'));
const WhatsAppSimulatorPage = lazy(() => import('@pages/communication/WhatsAppSimulatorPage'));
const CalendarPage = lazy(() => import('@pages/calendar/CalendarPage'));
const HomeworkPage = lazy(() => import('@pages/homework/HomeworkPage'));
const PTMPage = lazy(() => import('@pages/ptm/PTMPage'));

// Admin
const ReportsPage = lazy(() => import('@pages/reports/ReportsPage'));
const AuditLogsPage = lazy(() => import('@pages/admin/AuditLogsPage'));
const SettingsPage = lazy(() => import('@pages/admin/SettingsPage'));
const RolesPage = lazy(() => import('@pages/admin/RolesPage'));
const TemplatesPage = lazy(() => import('@pages/templates/TemplatesPage'));
const FullSettingsPage = lazy(() => import('@pages/settings/SettingsPage'));
const CredentialsPage = lazy(() => import('@pages/admin/CredentialsPage'));

// Portals
const StudentPortal = lazy(() => import('@pages/portals/StudentPortal'));
const ParentPortal = lazy(() => import('@pages/portals/ParentPortal'));
const TeacherPortal = lazy(() => import('@pages/portals/TeacherPortal'));

// Legal
const PrivacyPolicyPage = lazy(() => import('@pages/legal/PrivacyPolicyPage'));
const TermsPage = lazy(() => import('@pages/legal/TermsPage'));

// Public school website (per-school marketing site)
const PublicSiteLayout = lazy(() => import('@components/public/PublicSiteLayout'));
const SiteHomePage = lazy(() => import('@pages/site/SiteHomePage'));
const SiteAboutPage = lazy(() => import('@pages/site/SiteAboutPage'));
const SiteGalleryPage = lazy(() => import('@pages/site/SiteGalleryPage'));
const SiteNoticesPage = lazy(() => import('@pages/site/SiteNoticesPage'));
const SiteNoticeDetailPage = lazy(() => import('@pages/site/SiteNoticeDetailPage'));
const SiteEventsPage = lazy(() => import('@pages/site/SiteEventsPage'));
const SiteEnquiryPage = lazy(() => import('@pages/site/SiteEnquiryPage'));
const SiteContactPage = lazy(() => import('@pages/site/SiteContactPage'));
const SiteSectionPage = lazy(() => import('@pages/site/SiteSectionPage'));
const HostSiteGate = lazy(() => import('@pages/site/HostSiteGate'));
const WebsiteAdminPage = lazy(() => import('@pages/website/WebsiteAdminPage'));

// Custom-domain detection: only active when VITE_APP_HOSTS is explicitly set.
// Defaults to false so the admin app on the main domain is never affected.
const APP_HOSTS = (import.meta.env.VITE_APP_HOSTS || '')
  .split(',')
  .map((h: string) => h.trim())
  .filter(Boolean);
const IS_CUSTOM_DOMAIN =
  APP_HOSTS.length > 0 && !APP_HOSTS.includes(window.location.hostname);

// Not found
const NotFoundPage = lazy(() => import('@pages/NotFoundPage'));

const PageLoader: React.FC = () => (
  <div className="flex h-screen items-center justify-center">
    <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
  </div>
);

const AppRoutes: React.FC = () => {
  // On a recognized custom domain, the whole app IS the public school site.
  if (IS_CUSTOM_DOMAIN) {
    return (
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/admissions/apply/:slug" element={<PublicAdmissionApplyPage />} />
          <Route path="/admissions/status" element={<AdmissionStatusPage />} />
          <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/*" element={<HostSiteGate />} />
        </Routes>
      </Suspense>
    );
  }

  return (
  <Suspense fallback={<PageLoader />}>
    <Routes>
      {/* ── Public Routes ─────────────────────────────────────────────── */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/admissions/apply/:slug" element={<PublicAdmissionApplyPage />} />
      <Route path="/admissions/status" element={<AdmissionStatusPage />} />
      <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
      <Route path="/terms" element={<TermsPage />} />

      {/* ── Public School Website (path-based fallback) ───────────────── */}
      <Route path="/site/:slug" element={<PublicSiteLayout />}>
        <Route index element={<SiteHomePage />} />
        <Route path="about" element={<SiteAboutPage />} />
        <Route path="academics" element={<SiteSectionPage />} />
        <Route path="faculty" element={<SiteSectionPage />} />
        <Route path="achievements" element={<SiteSectionPage />} />
        <Route path="facilities" element={<SiteSectionPage />} />
        <Route path="downloads" element={<SiteSectionPage />} />
        <Route path="testimonials" element={<SiteSectionPage />} />
        <Route path="gallery" element={<SiteGalleryPage />} />
        <Route path="notices" element={<SiteNoticesPage />} />
        <Route path="notices/:noticeId" element={<SiteNoticeDetailPage />} />
        <Route path="events" element={<SiteEventsPage />} />
        <Route path="enquiry" element={<SiteEnquiryPage />} />
        <Route path="contact" element={<SiteContactPage />} />
      </Route>

      {/* ── Super Admin Routes ─────────────────────────────────────── */}
      <Route element={<PrivateRoute />}>
        <Route element={<SuperAdminLayout />}>
          <Route path="/super-admin/dashboard" element={<SuperAdminPage />} />
          <Route path="/super-admin" element={<Navigate to="/super-admin/dashboard" replace />} />
        </Route>
      </Route>

      {/* ── Protected Routes ──────────────────────────────────────────── */}
      <Route element={<PrivateRoute />}>
        <Route element={<AppLayout />}>
          {/* Default → dashboard */}
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Academic */}
          <Route path="/admin/academic-years" element={<AcademicYearsPage />} />
          <Route path="/admin/admissions" element={<AdmissionsPage />} />

          {/* Classes */}
          <Route path="/admin/classes" element={<ClassesPage />} />
          <Route path="/admin/subjects" element={<SubjectsPage />} />
          <Route path="/admin/timetable" element={<TimetablePage />} />

          {/* People */}
          <Route path="/admin/students" element={<StudentsPage />} />
          <Route path="/students/:studentId" element={<StudentDetailPage />} />
          <Route path="/admin/staff" element={<StaffPage />} />
          <Route path="/admin/staff/new" element={<StaffFormPage />} />
          <Route path="/admin/staff/departments" element={<DepartmentsPage />} />
          <Route path="/admin/staff/:staffId" element={<StaffDetailPage />} />
          <Route path="/admin/staff/:staffId/edit" element={<StaffFormPage />} />
          <Route path="/admin/payroll" element={<PayrollPage />} />
          <Route path="/admin/leaves" element={<LeavesPage />} />

          {/* Operations */}
          <Route path="/admin/attendance" element={<AttendancePage />} />
          <Route path="/admin/fees" element={<FeesPage />} />
          <Route path="/admin/fees-advanced" element={<AdvancedFeesPage />} />
          <Route path="/admin/personal-expenses" element={<PersonalExpensesPage />} />
          <Route path="/admin/exams" element={<ExamsPage />} />
          <Route path="/admin/library" element={<LibraryPage />} />
          <Route path="/admin/transport" element={<TransportPage />} />
          <Route path="/admin/inventory" element={<InventoryPage />} />
          <Route path="/admin/vendor-inventory" element={<VendorInventoryPage />} />
          <Route path="/admin/accounting" element={<AccountingPage />} />

          {/* Communication */}
          <Route path="/admin/communication" element={<CommunicationPage />} />
          <Route path="/admin/whatsapp-test" element={<WhatsAppSimulatorPage />} />
          <Route path="/admin/calendar" element={<CalendarPage />} />
          <Route path="/admin/homework" element={<HomeworkPage />} />
          <Route path="/admin/ptm" element={<PTMPage />} />

          {/* Admin */}
          <Route path="/admin/reports" element={<ReportsPage />} />
          <Route path="/admin/audit-logs" element={<AuditLogsPage />} />
          <Route path="/admin/settings" element={<SettingsPage />} />
          <Route path="/admin/settings/advanced" element={<FullSettingsPage />} />
          <Route path="/admin/roles" element={<RolesPage />} />
          <Route path="/admin/templates" element={<TemplatesPage />} />
          <Route path="/admin/credentials" element={<CredentialsPage />} />
          <Route path="/admin/website" element={<WebsiteAdminPage />} />
        </Route>

        {/* ── Portals ────────────────────────────────────────────────── */}
        <Route path="/student/*" element={<StudentPortal />} />
        <Route path="/parent/*" element={<ParentPortal />} />
        <Route path="/teacher/*" element={<TeacherPortal />} />
      </Route>

      {/* ── Catch-all ─────────────────────────────────────────────────── */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  </Suspense>
  );
};

export default AppRoutes;
