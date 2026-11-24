/**
 * RetainIQ Customer Retention Intelligence System
 * Administrator Management Portal (Phase 8.4.6 & Stage 6 Ink & Slate Transformation)
 *
 * Requirements:
 * - Enterprise Ink & Slate design system with restrained Precision Cobalt accents.
 * - Deep ink typography, clean white surfaces, cool slate backgrounds, hairline borders.
 * - Real backend connection via apiClient.admin:
 *   - GET /api/v1/admin/me (cryptographic backend verification)
 *   - GET /api/v1/admin/stats (aggregated real metrics)
 *   - GET /api/v1/admin/employees (search, status filter, pagination)
 *   - GET /api/v1/admin/employees/pending (pending registration requests)
 *   - GET /api/v1/admin/employees/{id} (inspect employee details)
 *   - POST /api/v1/admin/employees/invite (pre-authorize invitation)
 *   - POST /api/v1/admin/employees/{id}/approve (approve registration with confirmation)
 *   - POST /api/v1/admin/employees/{id}/reject (reject with mandatory reason)
 * - Strict server-side administrator authorization: non-admin accounts receive 403 with dedicated Access Denied screen.
 * - Responsive at 1440px, 1024px, 768px, 390px.
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Users,
  UserCheck,
  UserX,
  UserPlus,
  Clock,
  Search,
  Filter,
  RefreshCw,
  LogOut,
  ArrowLeft,
  ArrowRight,
  Check,
  X,
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Menu,
  Eye,
  Building2,
  Lock,
  Loader2,
  UserMinus,
  Sparkles,
  Server,
  Cpu,
  Database,
  KeyRound,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { apiClient } from "../lib/apiClient";
import { supabase } from "../lib/supabase";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { Container } from "../components/ui/Container";
import { ThemeToggle } from "../components/ui/ThemeToggle";

export function AdminPortalPage({ onNavigate }) {
  const { session, user, isLoading: isAuthLoading } = useAuth();

  // Navigation & View State: 'overview' | 'requests' | 'directory'
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== "undefined") {
      const p = new URLSearchParams(window.location.search).get("tab");
      if (p && ["overview", "requests", "directory"].includes(p)) {
        return p;
      }
    }
    return "overview";
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Dynamic Page Titles for Administrator Portal
  useEffect(() => {
    const titles = {
      overview: "Administrator Portal | RetainIQ",
      requests: "Pending Registrations | RetainIQ",
      directory: "Employee Directory | RetainIQ",
    };
    document.title = titles[activeTab] || "Administrator Portal | RetainIQ";
  }, [activeTab]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  // Verification & Auth Guard State
  const [isVerifyingAdmin, setIsVerifyingAdmin] = useState(true);
  const [adminProfile, setAdminProfile] = useState(null);
  const [authForbiddenError, setAuthForbiddenError] = useState(null);

  // Global Feedback Banner
  const [feedback, setFeedback] = useState(null); // { type: 'success' | 'error', message: string }

  // ---------------------------------------------------------------------------
  // Data States
  // ---------------------------------------------------------------------------
  const [stats, setStats] = useState(null);
  const [isStatsLoading, setIsStatsLoading] = useState(false);

  const [pendingRequests, setPendingRequests] = useState([]);
  const [isPendingLoading, setIsPendingLoading] = useState(false);

  const [directoryEmployees, setDirectoryEmployees] = useState([]);
  const [isDirectoryLoading, setIsDirectoryLoading] = useState(false);
  const [directoryStatusFilter, setDirectoryStatusFilter] = useState("ALL");
  const [directorySearchQuery, setDirectorySearchQuery] = useState("");
  const [directoryPage, setDirectoryPage] = useState(0);
  const PAGE_SIZE = 15;

  // System Infrastructure Health State
  const [systemHealth, setSystemHealth] = useState({
    isLoading: true,
    gateway: { status: "loading", label: "Checking Gateway..." },
    database: { status: "loading", label: "Checking Storage..." },
    model: { status: "loading", label: "Checking Artifacts..." },
    checksum: "24F1F0E3...3438F301",
    threshold: "tau = 0.50",
  });

  const loadSystemHealth = useCallback(async () => {
    try {
      const [gwRes, mlRes, dbRes] = await Promise.allSettled([
        apiClient.get("/api/v1/health"),
        apiClient.ml.getStatus(),
        apiClient.database.getHealth(),
      ]);

      const gwOk = gwRes.status === "fulfilled" && gwRes.value?.data?.status === "healthy";
      const mlOk = mlRes.status === "fulfilled" && mlRes.value?.data?.rf_pipeline_loaded;
      const dbOk = dbRes.status === "fulfilled" && dbRes.value?.data?.is_connected;

      setSystemHealth({
        isLoading: false,
        gateway: {
          status: gwOk ? "healthy" : "error",
          label: gwOk ? "Online (HTTP 200)" : "Gateway Offline",
        },
        database: {
          status: dbOk ? "healthy" : dbRes.status === "fulfilled" ? "degraded" : "error",
          label: dbOk ? "Connected (RLS Active)" : "Storage Degraded",
        },
        model: {
          status: mlOk ? "healthy" : "error",
          label: mlOk ? "Locked (Config D RF)" : "Model Offline",
        },
        checksum: mlRes.status === "fulfilled" && mlRes.value?.data?.rf_model_sha256
          ? `${mlRes.value.data.rf_model_sha256.slice(0, 8)}...${mlRes.value.data.rf_model_sha256.slice(-8)}`
          : "24F1F0E3...3438F301",
        threshold: mlRes.status === "fulfilled" && mlRes.value?.data?.decision_threshold
          ? `tau = ${mlRes.value.data.decision_threshold.toFixed(2)}`
          : "tau = 0.50",
      });
    } catch {
      setSystemHealth((prev) => ({
        ...prev,
        isLoading: false,
        gateway: { status: "error", label: "Connection Failed" },
        database: { status: "error", label: "Connection Failed" },
        model: { status: "error", label: "Connection Failed" },
      }));
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Modals & Action States
  // ---------------------------------------------------------------------------
  // Inspection Modal
  const [inspectingEmployee, setInspectingEmployee] = useState(null);

  // Approval Modal
  const [approvingEmployee, setApprovingEmployee] = useState(null);
  const [approvalNotes, setApprovalNotes] = useState("");
  const [isSubmittingApproval, setIsSubmittingApproval] = useState(false);

  // Rejection Modal
  const [rejectingEmployee, setRejectingEmployee] = useState(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [rejectionError, setRejectionError] = useState(null);
  const [isSubmittingRejection, setIsSubmittingRejection] = useState(false);

  // Invite Modal
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    employee_id: "",
    work_email: "",
    full_name: "",
    department: "Customer Success",
    notes: "",
  });
  const [inviteErrors, setInviteErrors] = useState({});
  const [isSubmittingInvite, setIsSubmittingInvite] = useState(false);

  // Handle Escape key to close open modals
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        if (inspectingEmployee) setInspectingEmployee(null);
        if (approvingEmployee && !isSubmittingApproval) setApprovingEmployee(null);
        if (rejectingEmployee && !isSubmittingRejection) setRejectingEmployee(null);
        if (isInviteModalOpen && !isSubmittingInvite) setIsInviteModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    inspectingEmployee,
    approvingEmployee,
    rejectingEmployee,
    isInviteModalOpen,
    isSubmittingApproval,
    isSubmittingRejection,
    isSubmittingInvite,
  ]);

  // ---------------------------------------------------------------------------
  // 1. Verify Administrator Session with Backend
  // ---------------------------------------------------------------------------
  const verifyAdminAccess = useCallback(async () => {
    if (!session?.access_token || !user) {
      setIsVerifyingAdmin(false);
      return;
    }

    setIsVerifyingAdmin(true);
    setAuthForbiddenError(null);

    try {
      const res = await apiClient.admin.getProfile();
      if (res?.success && res?.data?.is_admin) {
        setAdminProfile(res.data);
      } else {
        setAuthForbiddenError("Your account lacks administrator authorization.");
      }
    } catch (err) {
      if (err.status === 403 || err.isForbiddenError) {
        setAuthForbiddenError(
          "Access denied: Account is authenticated but does not possess verified RetainIQ administrator privileges."
        );
      } else if (err.status === 401 || err.isAuthError) {
        setAuthForbiddenError("Authentication session expired or invalid. Please sign in again.");
      } else {
        setAuthForbiddenError(`Backend authorization service error: ${err.message}`);
      }
    } finally {
      setIsVerifyingAdmin(false);
    }
  }, [session, user]);

  useEffect(() => {
    verifyAdminAccess();
  }, [verifyAdminAccess]);

  // ---------------------------------------------------------------------------
  // 2. Load Stats
  // ---------------------------------------------------------------------------
  const loadStats = useCallback(async () => {
    if (!adminProfile) return;
    setIsStatsLoading(true);
    try {
      const res = await apiClient.admin.getStats();
      if (res?.success && res?.data) {
        setStats(res.data);
      }
    } catch (err) {
      console.error("[RetainIQ Admin] Failed to fetch stats:", err);
    } finally {
      setIsStatsLoading(false);
    }
  }, [adminProfile]);

  // ---------------------------------------------------------------------------
  // 3. Load Pending Requests
  // ---------------------------------------------------------------------------
  const loadPendingRequests = useCallback(async () => {
    if (!adminProfile) return;
    setIsPendingLoading(true);
    try {
      const res = await apiClient.admin.getPendingEmployees({ limit: 100, offset: 0 });
      if (res?.success && Array.isArray(res?.data)) {
        setPendingRequests(res.data);
      }
    } catch (err) {
      console.error("[RetainIQ Admin] Failed to fetch pending requests:", err);
    } finally {
      setIsPendingLoading(false);
    }
  }, [adminProfile]);

  // ---------------------------------------------------------------------------
  // 4. Load Employee Directory
  // ---------------------------------------------------------------------------
  const loadDirectory = useCallback(async () => {
    if (!adminProfile) return;
    setIsDirectoryLoading(true);
    try {
      const res = await apiClient.admin.listEmployees({
        status: directoryStatusFilter,
        search: directorySearchQuery,
        limit: PAGE_SIZE,
        offset: directoryPage * PAGE_SIZE,
      });
      if (res?.success && Array.isArray(res?.data)) {
        setDirectoryEmployees(res.data);
      }
    } catch (err) {
      console.error("[RetainIQ Admin] Failed to fetch employee directory:", err);
    } finally {
      setIsDirectoryLoading(false);
    }
  }, [adminProfile, directoryStatusFilter, directorySearchQuery, directoryPage]);

  // Trigger Data Loads on Tab Change or Auth Success
  useEffect(() => {
    if (adminProfile) {
      loadStats();
      if (activeTab === "overview" || activeTab === "requests") {
        loadPendingRequests();
      }
      if (activeTab === "overview" || activeTab === "directory") {
        loadDirectory();
      }
      if (activeTab === "overview") {
        loadSystemHealth();
      }
    }
  }, [adminProfile, activeTab, loadStats, loadPendingRequests, loadDirectory, loadSystemHealth]);

  // Auto-dismiss Feedback
  useEffect(() => {
    if (feedback) {
      const timer = setTimeout(() => setFeedback(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [feedback]);

  // ---------------------------------------------------------------------------
  // Action Handlers: Approve, Reject, Invite
  // ---------------------------------------------------------------------------
  const handleConfirmApproval = async () => {
    if (!approvingEmployee || isSubmittingApproval) return;
    setIsSubmittingApproval(true);

    try {
      const res = await apiClient.admin.approveEmployee(approvingEmployee.employee_id, {
        notes: approvalNotes.trim() || undefined,
      });

      if (res?.success) {
        setFeedback({
          type: "success",
          message: `Employee ${approvingEmployee.employee_id} (${approvingEmployee.work_email}) has been approved successfully.`,
        });
        setApprovingEmployee(null);
        setApprovalNotes("");
        // Refresh data
        loadPendingRequests();
        loadStats();
        loadDirectory();
      }
    } catch (err) {
      setFeedback({
        type: "error",
        message: err.data?.error?.message || err.message || "Failed to approve employee.",
      });
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  const handleConfirmRejection = async () => {
    if (!rejectingEmployee || isSubmittingRejection) return;
    const cleanReason = rejectionReason.trim();

    if (!cleanReason || cleanReason.length < 3) {
      setRejectionError("A meaningful rejection reason of at least 3 characters is mandatory.");
      return;
    }

    setIsSubmittingRejection(true);
    setRejectionError(null);

    try {
      const res = await apiClient.admin.rejectEmployee(rejectingEmployee.employee_id, {
        reason: cleanReason,
      });

      if (res?.success) {
        setFeedback({
          type: "success",
          message: `Employee ${rejectingEmployee.employee_id} registration has been rejected.`,
        });
        setRejectingEmployee(null);
        setRejectionReason("");
        // Refresh data
        loadPendingRequests();
        loadStats();
        loadDirectory();
      }
    } catch (err) {
      setRejectionError(err.data?.error?.message || err.message || "Failed to reject employee.");
    } finally {
      setIsSubmittingRejection(false);
    }
  };

  const handleInviteSubmit = async (e) => {
    e.preventDefault();
    if (isSubmittingInvite) return;

    const errors = {};
    const cleanId = inviteForm.employee_id.trim().toUpperCase();
    const cleanEmail = inviteForm.work_email.trim().toLowerCase();

    if (!cleanId || cleanId.length < 3) {
      errors.employee_id = "Employee ID must be at least 3 characters.";
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!cleanEmail || !emailRegex.test(cleanEmail)) {
      errors.work_email = "Valid enterprise work email is required.";
    }

    if (Object.keys(errors).length > 0) {
      setInviteErrors(errors);
      return;
    }

    setIsSubmittingInvite(true);
    setInviteErrors({});

    try {
      const payload = {
        employee_id: cleanId,
        work_email: cleanEmail,
        full_name: inviteForm.full_name.trim() || undefined,
        department: inviteForm.department.trim() || "Customer Success",
        notes: inviteForm.notes.trim() || undefined,
      };

      const res = await apiClient.admin.inviteEmployee(payload);
      if (res?.success) {
        setFeedback({
          type: "success",
          message: `Employee invitation for ${cleanId} (${cleanEmail}) pre-authorized successfully.`,
        });
        setIsInviteModalOpen(false);
        setInviteForm({
          employee_id: "",
          work_email: "",
          full_name: "",
          department: "Customer Success",
          notes: "",
        });
        loadStats();
        loadDirectory();
      }
    } catch (err) {
      setInviteErrors({
        submit: err.data?.error?.message || err.message || "Failed to create invitation.",
      });
    } finally {
      setIsSubmittingInvite(false);
    }
  };

  const handleSignOut = async () => {
    try {
      if (supabase) {
        await supabase.auth.signOut();
      }
    } catch (err) {
      console.error("[RetainIQ Admin] Sign out error:", err);
    } finally {
      setAdminProfile(null);
      if (onNavigate) {
        onNavigate("/employee/login");
      } else {
        window.location.pathname = "/employee/login";
      }
    }
  };

  // Helper for Status Badges
  const renderStatusBadge = (status) => {
    const s = String(status || "").toUpperCase();
    switch (s) {
      case "APPROVED":
        return <Badge variant="success" dot size="sm">APPROVED</Badge>;
      case "PENDING":
        return <Badge variant="warning" dot size="sm">PENDING</Badge>;
      case "INVITED":
        return <Badge variant="primary" dot size="sm">INVITED</Badge>;
      case "REJECTED":
        return <Badge variant="danger" dot size="sm">REJECTED</Badge>;
      case "SUSPENDED":
        return <Badge variant="neutral" dot size="sm">SUSPENDED</Badge>;
      default:
        return <Badge variant="neutral" size="sm">{s}</Badge>;
    }
  };

  // ---------------------------------------------------------------------------
  // AUTH GUARD VIEW 1: LOADING STATE
  // ---------------------------------------------------------------------------
  if (isAuthLoading || isVerifyingAdmin) {
    return (
      <div className="min-h-screen bg-bg flex flex-col items-center justify-center p-6 text-center">
        <div className="w-14 h-14 rounded-2xl bg-surface border border-border flex items-center justify-center shadow-subtle mb-4">
          <ShieldCheck className="w-7 h-7 text-electric animate-spin" />
        </div>
        <h2 className="font-heading font-semibold text-lg text-midnight tracking-tight">
          Verifying Administrator Privileges
        </h2>
        <p className="text-xs text-text-secondary mt-1 font-mono max-w-sm leading-relaxed">
          Cryptographically evaluating JWT against Supabase JWKS & server policy...
        </p>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // AUTH GUARD VIEW 2: UNAUTHENTICATED
  // ---------------------------------------------------------------------------
  if (!session || !user) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center p-4 sm:p-6">
        <Card variant="surface" className="max-w-md w-full text-center p-7 sm:p-8 space-y-6 shadow-card border-border">
          <div className="w-13 h-13 mx-auto rounded-2xl bg-amber-50 text-amber-600 border border-amber-200/80 flex items-center justify-center">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 text-[10px] font-mono font-medium uppercase rounded-md bg-amber-50 text-amber-800 border border-amber-200 inline-block mb-2.5">
              AUTHENTICATION REQUIRED
            </span>
            <h2 className="font-heading text-xl sm:text-2xl font-semibold text-midnight tracking-tight">
              Administrator Login Required
            </h2>
            <p className="text-xs text-text-secondary mt-2 leading-relaxed">
              The RetainIQ Administrator Portal requires an active enterprise employee session with verified administrator authorization.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <Button
              variant="primary"
              size="md"
              onClick={() => onNavigate ? onNavigate("/employee/login") : (window.location.pathname = "/employee/login")}
              className="w-full justify-center text-xs font-medium"
            >
              Proceed to Employee Sign In
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate ? onNavigate("/") : (window.location.pathname = "/")}
              icon={ArrowLeft}
              className="w-full justify-center text-xs text-text-secondary hover:text-midnight"
            >
              Return to Public Showcase
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // AUTH GUARD VIEW 3: 403 FORBIDDEN / NON-ADMINISTRATOR ACCESS DENIED
  // ---------------------------------------------------------------------------
  if (authForbiddenError || !adminProfile) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center p-4 sm:p-6">
        <Card variant="surface" className="max-w-lg w-full text-center p-7 sm:p-8 space-y-6 border-red-200 shadow-card">
          <div className="w-13 h-13 mx-auto rounded-2xl bg-red-50 text-red-600 border border-red-200 flex items-center justify-center">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 text-[10px] font-mono font-medium uppercase rounded-md bg-red-50 text-red-800 border border-red-200 inline-block mb-2.5">
              403 FORBIDDEN • ACCESS DENIED
            </span>
            <h2 className="font-heading text-xl sm:text-2xl font-semibold text-midnight tracking-tight">
              Administrator Privileges Required
            </h2>
            <p className="text-xs text-text-secondary mt-2 leading-relaxed">
              {authForbiddenError || "Access to the Administrator Management Portal is strictly restricted to designated RetainIQ administrators."}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-border text-xs text-left space-y-2">
            <div className="flex justify-between items-center text-text-muted">
              <span>Authenticated Identity:</span>
              <span className="font-mono font-medium text-midnight text-[11px] truncate max-w-[220px]">
                {user.email || "Unknown email"}
              </span>
            </div>
            <div className="flex justify-between items-center text-text-muted">
              <span>Subject UUID:</span>
              <span className="font-mono text-text-secondary text-[10px] truncate max-w-[220px]">
                {user.id}
              </span>
            </div>
            <div className="flex justify-between items-center text-text-muted">
              <span>Security Status:</span>
              <span className="font-medium text-red-600">Non-Administrator Account</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 text-xs text-left">
            <p className="text-[11px] leading-relaxed">
              If you require administrative privileges to approve employee registrations or pre-authorize employee invitations, please contact your organization system administrator.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <Button
              variant="primary"
              size="md"
              onClick={() => onNavigate ? onNavigate("/employee/dashboard") : (window.location.pathname = "/employee/dashboard")}
              icon={ArrowRight}
              iconPosition="right"
              className="w-full justify-center text-xs font-medium"
            >
              Go to Employee Dashboard (/employee/dashboard)
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={handleSignOut}
              icon={LogOut}
              className="w-full justify-center text-xs font-medium text-text-secondary hover:text-midnight"
            >
              Sign Out of This Account
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate ? onNavigate("/") : (window.location.pathname = "/")}
              icon={ArrowLeft}
              className="w-full justify-center text-xs text-text-secondary hover:text-midnight"
            >
              Return to Public Showcase
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // MAIN ADMINISTRATOR PORTAL UI
  // ---------------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-bg text-text-primary flex flex-col selection:bg-electric selection:text-white">
      {/* ==================================================================== */}
      {/* Top Application Header                                                */}
      {/* ==================================================================== */}
      <header className="border-b border-border bg-surface/95 backdrop-blur-sm sticky top-0 z-30">
        <Container size="full" className="px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          {/* Brand & Identity */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate ? onNavigate("/") : (window.location.pathname = "/")}
              className="flex items-center gap-3 group text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-electric rounded-xl p-1"
              aria-label="Return to Public Showcase"
            >
              <div className="w-10 h-10 rounded-xl bg-midnight flex items-center justify-center shadow-subtle border border-slate-700 transition-colors">
                <svg className="w-5 h-5 text-electric" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 12v-3a8 8 0 0 1 16 0v3" />
                  <path d="M9 18l3 3 3-3" />
                  <circle cx="12" cy="12" r="3" fill="#0052CC" />
                </svg>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-heading font-semibold text-lg sm:text-xl text-midnight tracking-tight">
                    Retain<span className="text-electric">IQ</span>
                  </span>
                  <span className="px-2 py-0.5 text-[9.5px] font-mono font-medium uppercase rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                    ADMIN
                  </span>
                </div>
                <span className="text-[10px] font-mono text-text-muted tracking-wider uppercase">
                  Enterprise Management Portal
                </span>
              </div>
            </button>
          </div>

          {/* Desktop Administrator Badge & Actions */}
          <div className="hidden md:flex items-center gap-3.5">
            {/* Quick Invite Button */}
            <Button
              variant="primary"
              size="sm"
              icon={UserPlus}
              onClick={() => setIsInviteModalOpen(true)}
              className="text-xs font-medium shadow-subtle"
            >
              Invite Employee
            </Button>

            {/* Admin Identity Pill */}
            <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-surface border border-border text-xs shadow-subtle">
              <div className="w-2 h-2 rounded-full bg-success"></div>
              <div className="flex flex-col text-left">
                <span className="font-medium text-midnight leading-tight truncate max-w-[160px]">
                  {adminProfile.email || "Administrator"}
                </span>
                <span className="text-[9.5px] font-mono text-text-muted">
                  ADMINISTRATOR
                </span>
              </div>
            </div>

            {/* Theme Toggle */}
            <ThemeToggle size="sm" />

            {/* Sign Out */}
            <Button
              variant="outline"
              size="sm"
              icon={LogOut}
              onClick={handleSignOut}
              className="text-xs text-text-secondary hover:text-midnight font-medium border-border"
            >
              Sign Out
            </Button>
          </div>

          {/* Mobile Actions: Theme Toggle + Menu */}
          <div className="flex md:hidden items-center gap-2">
            <ThemeToggle size="sm" />
            <Button
              variant="primary"
              size="sm"
              icon={UserPlus}
              onClick={() => setIsInviteModalOpen(true)}
              className="text-xs px-2.5 py-1.5"
            >
              Invite
            </Button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl border border-border bg-surface text-text-primary hover:bg-slate-50 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </Container>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border bg-surface px-4 py-4 space-y-4 shadow-elevated">
            <div className="p-3 rounded-xl bg-slate-50 border border-border text-xs space-y-1">
              <span className="text-text-muted">Signed In Administrator:</span>
              <p className="font-mono font-medium text-midnight truncate">{adminProfile.email}</p>
            </div>
            <div className="flex flex-col gap-1.5">
              <button
                onClick={() => { setActiveTab("overview"); setMobileMenuOpen(false); }}
                className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-heading font-medium transition-colors ${activeTab === "overview"
                  ? "bg-slate-100 text-midnight border border-border shadow-subtle font-semibold"
                  : "text-text-secondary hover:bg-slate-50"
                  }`}
              >
                Overview
              </button>
              <button
                onClick={() => { setActiveTab("requests"); setMobileMenuOpen(false); }}
                className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-heading font-medium flex items-center justify-between transition-colors ${activeTab === "requests"
                  ? "bg-slate-100 text-midnight border border-border shadow-subtle font-semibold"
                  : "text-text-secondary hover:bg-slate-50"
                  }`}
              >
                <span>Employee Requests</span>
                {pendingRequests.length > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-100 text-amber-800 border border-amber-200">
                    {pendingRequests.length}
                  </span>
                )}
              </button>
              <button
                onClick={() => { setActiveTab("directory"); setMobileMenuOpen(false); }}
                className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-heading font-medium transition-colors ${activeTab === "directory"
                  ? "bg-slate-100 text-midnight border border-border shadow-subtle font-semibold"
                  : "text-text-secondary hover:bg-slate-50"
                  }`}
              >
                Employee Directory
              </button>
            </div>
            <div className="pt-2 border-t border-border flex flex-col gap-2">
              <div className="flex items-center justify-between px-1 py-1">
                <span className="text-xs font-mono text-text-muted">Appearance Theme</span>
                <ThemeToggle variant="pill" size="sm" />
              </div>
              <Button
                variant="outline"
                size="sm"
                icon={LogOut}
                onClick={handleSignOut}
                className="w-full justify-center text-xs"
              >
                Sign Out
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* Global Notification Feedback Banner */}
      {feedback && (
        <div className={`px-4 py-3 border-b text-xs flex items-center justify-between transition-all ${feedback.type === "success"
          ? "bg-emerald-50/90 border-emerald-200 text-emerald-800"
          : "bg-red-50/90 border-red-200 text-red-800"
          }`}>
          <Container size="full" className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {feedback.type === "success" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              )}
              <span className="font-medium">{feedback.message}</span>
            </div>
            <button
              onClick={() => setFeedback(null)}
              className="p-1 rounded hover:bg-black/5 text-current shrink-0"
              aria-label="Dismiss feedback"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </Container>
        </div>
      )}

      {/* ==================================================================== */}
      {/* Main Container with Sidebar + Content Layout                         */}
      {/* ==================================================================== */}
      <div className="flex-grow flex">
        {/* Desktop Sidebar Navigation */}
        <aside className="hidden md:flex flex-col w-64 border-r border-border bg-surface p-5 shrink-0 justify-between">
          <div className="space-y-6">
            <div>
              <span className="text-[10px] font-mono font-semibold tracking-wider text-text-muted uppercase block px-3 mb-2">
                MANAGEMENT
              </span>
              <nav className="space-y-1">
                <button
                  onClick={() => setActiveTab("overview")}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-heading transition-all ${activeTab === "overview"
                    ? "bg-slate-100 text-midnight border border-border shadow-subtle font-semibold"
                    : "text-text-secondary hover:text-midnight hover:bg-slate-50 border border-transparent font-medium"
                    }`}
                >
                  <Users className={`w-4 h-4 shrink-0 ${activeTab === "overview" ? "text-electric" : "text-text-muted"}`} />
                  <span>Overview</span>
                </button>

                <button
                  onClick={() => setActiveTab("requests")}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-heading transition-all ${activeTab === "requests"
                    ? "bg-slate-100 text-midnight border border-border shadow-subtle font-semibold"
                    : "text-text-secondary hover:text-midnight hover:bg-slate-50 border border-transparent font-medium"
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <Clock className={`w-4 h-4 shrink-0 ${activeTab === "requests" ? "text-electric" : "text-text-muted"}`} />
                    <span>Employee Requests</span>
                  </div>
                  {pendingRequests.length > 0 && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-100 text-amber-800 border border-amber-200">
                      {pendingRequests.length}
                    </span>
                  )}
                </button>

                <button
                  onClick={() => setActiveTab("directory")}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-heading transition-all ${activeTab === "directory"
                    ? "bg-slate-100 text-midnight border border-border shadow-subtle font-semibold"
                    : "text-text-secondary hover:text-midnight hover:bg-slate-50 border border-transparent font-medium"
                    }`}
                >
                  <Building2 className={`w-4 h-4 shrink-0 ${activeTab === "directory" ? "text-electric" : "text-text-muted"}`} />
                  <span>Employee Directory</span>
                </button>
              </nav>
            </div>

            <div>
              <span className="text-[10px] font-mono font-semibold tracking-wider text-text-muted uppercase block px-3 mb-2">
                ACTIONS
              </span>
              <div className="space-y-1">
                <button
                  onClick={() => setIsInviteModalOpen(true)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-heading font-medium text-text-secondary hover:text-midnight hover:bg-slate-50 border border-transparent transition-colors text-left"
                >
                  <UserPlus className="w-4 h-4 shrink-0 text-electric" />
                  <span>Pre-Authorize Invitation</span>
                </button>
                <button
                  onClick={() => {
                    loadStats();
                    loadPendingRequests();
                    loadDirectory();
                    setFeedback({ type: "success", message: "All administrative registry records refreshed." });
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-heading font-medium text-text-secondary hover:text-midnight hover:bg-slate-50 border border-transparent transition-colors text-left"
                >
                  <RefreshCw className="w-4 h-4 shrink-0 text-text-muted" />
                  <span>Refresh All Data</span>
                </button>
              </div>
            </div>
          </div>

          {/* Security Status Box */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-border text-[11px] space-y-1.5 text-text-secondary">
            <div className="flex items-center gap-1.5 font-heading font-semibold text-midnight text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Security Invariant</span>
            </div>
            <p className="leading-relaxed text-[10.5px]">
              Access control is enforced server-side. Unapproved accounts cannot query customer data.
            </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-grow p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {/* ================================================================ */}
          {/* TAB 1: OVERVIEW                                                  */}
          {/* ================================================================ */}
          {activeTab === "overview" && (
            <div className="space-y-8">
              {/* Header Title */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h1 className="font-heading font-semibold text-2xl sm:text-3xl text-midnight tracking-tight">
                    Administrator Overview
                  </h1>
                  <p className="text-xs text-text-secondary mt-1">
                    Real-time metrics, pending access reviews, and employee directory controls.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={RefreshCw}
                    loading={isStatsLoading}
                    onClick={() => {
                      loadStats();
                      loadPendingRequests();
                      loadDirectory();
                    }}
                    className="text-xs"
                  >
                    Refresh
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={UserPlus}
                    onClick={() => setIsInviteModalOpen(true)}
                    className="text-xs font-medium shadow-subtle"
                  >
                    Invite Employee
                  </Button>
                </div>
              </div>

              {/* KPI Statistics Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-6 gap-3.5 sm:gap-4">
                {/* Total */}
                <Card variant="surface" className="p-5 sm:p-6 space-y-2 border-border shadow-subtle">
                  <div className="flex items-center justify-between text-text-secondary">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider block font-medium">
                      Total Records
                    </span>
                    <Users className="w-4 h-4 text-text-muted" />
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="font-heading font-semibold text-2xl sm:text-3xl text-midnight tabular-nums">
                      {stats ? stats.total : "—"}
                    </span>
                    <span className="text-[10px] font-mono text-text-muted">REGISTRY</span>
                  </div>
                </Card>

                {/* Pending */}
                <Card variant="surface" className={`p-5 sm:p-6 space-y-2 shadow-subtle ${stats?.pending > 0 ? "border-amber-200/90 bg-amber-50/20" : "border-border"}`}>
                  <div className="flex items-center justify-between text-amber-800">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider block font-medium">
                      Pending Approval
                    </span>
                    <Clock className="w-4 h-4 text-amber-600" />
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="font-heading font-semibold text-2xl sm:text-3xl text-amber-700 tabular-nums">
                      {stats ? stats.pending : "—"}
                    </span>
                    {stats?.pending > 0 && (
                      <span className="px-1.5 py-0.5 rounded text-[9.5px] font-mono font-medium bg-amber-100 text-amber-800">
                        ACTION
                      </span>
                    )}
                  </div>
                </Card>

                {/* Approved */}
                <Card variant="surface" className="p-5 sm:p-6 space-y-2 border-border shadow-subtle">
                  <div className="flex items-center justify-between text-emerald-800">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider block font-medium">
                      Approved
                    </span>
                    <UserCheck className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="font-heading font-semibold text-2xl sm:text-3xl text-emerald-700 tabular-nums">
                      {stats ? stats.approved : "—"}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-700 font-medium">ACTIVE</span>
                  </div>
                </Card>

                {/* Invited */}
                <Card variant="surface" className="p-5 sm:p-6 space-y-2 border-border shadow-subtle">
                  <div className="flex items-center justify-between text-electric">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider block font-medium">
                      Invited
                    </span>
                    <UserPlus className="w-4 h-4 text-electric" />
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="font-heading font-semibold text-2xl sm:text-3xl text-electric tabular-nums">
                      {stats ? stats.invited : "—"}
                    </span>
                    <span className="text-[10px] font-mono text-electric font-medium">PRE-AUTH</span>
                  </div>
                </Card>

                {/* Rejected */}
                <Card variant="surface" className="p-5 sm:p-6 space-y-2 border-border shadow-subtle">
                  <div className="flex items-center justify-between text-red-800">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider block font-medium">
                      Rejected
                    </span>
                    <UserX className="w-4 h-4 text-red-600" />
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="font-heading font-semibold text-2xl sm:text-3xl text-red-700 tabular-nums">
                      {stats ? stats.rejected : "—"}
                    </span>
                    <span className="text-[10px] font-mono text-red-700 font-medium">DENIED</span>
                  </div>
                </Card>

                {/* Suspended */}
                <Card variant="surface" className="p-5 sm:p-6 space-y-2 border-border shadow-subtle">
                  <div className="flex items-center justify-between text-text-secondary">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider block font-medium">
                      Suspended
                    </span>
                    <UserMinus className="w-4 h-4 text-text-muted" />
                  </div>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="font-heading font-semibold text-2xl sm:text-3xl text-text-secondary tabular-nums">
                      {stats ? stats.suspended : "—"}
                    </span>
                    <span className="text-[10px] font-mono text-text-muted">INACTIVE</span>
                  </div>
                </Card>
              </div>

              {/* System Infrastructure & Operational Health */}
              <div className="p-5 sm:p-6 rounded-2xl bg-surface border border-border shadow-subtle space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <Server className="w-4 h-4 text-electric" />
                    <h2 className="font-heading font-semibold text-sm text-midnight">
                      Enterprise System & ML Infrastructure State
                    </h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-success"></span>
                    <span className="text-[10px] font-mono text-text-muted uppercase">Audit Status: Verified & Locked</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-border space-y-1">
                    <span className="text-[10.5px] font-mono text-text-muted uppercase">FastAPI API Gateway</span>
                    <p className="font-semibold text-midnight flex items-center gap-1.5">
                      {systemHealth.gateway.status === "loading" ? (
                        <Loader2 className="w-3.5 h-3.5 text-text-muted animate-spin" />
                      ) : systemHealth.gateway.status === "healthy" ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-success" />
                      ) : (
                        <AlertCircle className="w-3.5 h-3.5 text-red-600" />
                      )}
                      <span>{systemHealth.gateway.label}</span>
                    </p>
                    <span className="text-[10px] text-text-secondary">Port 8000 • JWT Bearer Auth</span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-border space-y-1">
                    <span className="text-[10.5px] font-mono text-text-muted uppercase">Supabase Identity & DB</span>
                    <p className="font-semibold text-midnight flex items-center gap-1.5">
                      {systemHealth.database.status === "loading" ? (
                        <Loader2 className="w-3.5 h-3.5 text-text-muted animate-spin" />
                      ) : systemHealth.database.status === "healthy" ? (
                        <Database className="w-3.5 h-3.5 text-electric" />
                      ) : (
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                      )}
                      <span>{systemHealth.database.label}</span>
                    </p>
                    <span className="text-[10px] text-text-secondary">Row Level Security Enforced</span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-border space-y-1">
                    <span className="text-[10.5px] font-mono text-text-muted uppercase">ML Retention Model</span>
                    <p className="font-semibold text-midnight flex items-center gap-1.5">
                      {systemHealth.model.status === "loading" ? (
                        <Loader2 className="w-3.5 h-3.5 text-text-muted animate-spin" />
                      ) : systemHealth.model.status === "healthy" ? (
                        <Cpu className="w-3.5 h-3.5 text-electric" />
                      ) : (
                        <AlertCircle className="w-3.5 h-3.5 text-red-600" />
                      )}
                      <span>{systemHealth.model.label}</span>
                    </p>
                    <span className="text-[10px] font-mono text-text-secondary">{systemHealth.threshold} • 43 Raw Features</span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-border space-y-1">
                    <span className="text-[10.5px] font-mono text-text-muted uppercase">Artifact SHA-256</span>
                    <p className="font-mono font-medium text-midnight text-[11px] truncate" title="24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301">
                      {systemHealth.checksum}
                    </p>
                    <span className="text-[10px] text-text-secondary">KMeans K=5 Persona Scaler</span>
                  </div>
                </div>
              </div>

              {/* Pending Requests Callout Widget */}
              {pendingRequests.length > 0 ? (
                <div className="p-6 sm:p-7 rounded-2xl bg-amber-50/60 border border-amber-200/80 text-amber-950 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-900 border border-amber-200 flex items-center justify-center shrink-0 mt-0.5">
                      <Clock className="w-5 h-5 text-amber-700" />
                    </div>
                    <div>
                      <h3 className="font-heading font-semibold text-sm text-amber-950">
                        {pendingRequests.length} Employee Registration Request{pendingRequests.length > 1 ? "s" : ""} Awaiting Review
                      </h3>
                      <p className="text-xs text-amber-800 mt-0.5">
                        Applicants have completed registration and require administrator verification before access is granted.
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setActiveTab("requests")}
                    className="bg-amber-600 hover:bg-amber-700 text-white shadow-subtle shrink-0 text-xs font-medium"
                  >
                    Review Pending Requests
                  </Button>
                </div>
              ) : (
                <div className="p-6 sm:p-7 rounded-2xl bg-surface border border-border text-text-secondary flex items-center gap-3 shadow-subtle">
                  <CheckCircle2 className="w-5 h-5 text-success shrink-0" />
                  <p className="text-xs leading-relaxed">
                    <span className="font-semibold text-midnight">Queue Clear:</span> All employee registration requests have been reviewed. There are no registrations pending administrator approval.
                  </p>
                </div>
              )}

              {/* Recent Registry Snippet */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-heading font-semibold text-base text-midnight">
                    Recent Registry Records
                  </h2>
                  <button
                    onClick={() => setActiveTab("directory")}
                    className="text-xs font-semibold text-electric hover:underline"
                  >
                    View All in Directory →
                  </button>
                </div>

                <div className="bg-surface border border-border rounded-2xl shadow-subtle overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50/80 border-b border-border text-text-muted font-mono uppercase text-[10px] tracking-wider">
                        <tr>
                          <th className="py-3 px-4.5">Employee ID</th>
                          <th className="py-3 px-4.5">Work Email</th>
                          <th className="py-3 px-4.5">Department</th>
                          <th className="py-3 px-4.5">Status</th>
                          <th className="py-3 px-4.5 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {directoryEmployees.slice(0, 5).map((emp) => (
                          <tr key={emp.employee_id} className="hover:bg-slate-50/50 transition-colors">
                            <td className="py-3.5 px-4.5 font-mono font-medium text-midnight">
                              {emp.employee_id}
                            </td>
                            <td className="py-3.5 px-4.5 text-text-primary">
                              {emp.work_email}
                            </td>
                            <td className="py-3.5 px-4.5 text-text-secondary">
                              {emp.department || "Customer Success"}
                            </td>
                            <td className="py-3.5 px-4.5">
                              {renderStatusBadge(emp.status)}
                            </td>
                            <td className="py-3.5 px-4.5 text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                icon={Eye}
                                onClick={() => setInspectingEmployee(emp)}
                                className="text-xs text-text-secondary hover:text-midnight"
                              >
                                View
                              </Button>
                            </td>
                          </tr>
                        ))}
                        {directoryEmployees.length === 0 && (
                          <tr>
                            <td colSpan="5" className="py-8 text-center text-text-muted">
                              No employee records found.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 2: EMPLOYEE REQUESTS (PENDING APPROVALS)                     */}
          {/* ================================================================ */}
          {activeTab === "requests" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h1 className="font-heading font-semibold text-2xl sm:text-3xl text-midnight tracking-tight">
                    Pending Employee Requests
                  </h1>
                  <p className="text-xs text-text-secondary mt-1">
                    Review and authorize employee access requests. Approval grants access to protected customer intelligence tools.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  icon={RefreshCw}
                  loading={isPendingLoading}
                  onClick={loadPendingRequests}
                  className="text-xs"
                >
                  Refresh Requests
                </Button>
              </div>

              {/* Requests List */}
              {isPendingLoading ? (
                <div className="p-12 text-center text-xs text-text-muted flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-electric" /> Loading pending registrations...
                </div>
              ) : pendingRequests.length === 0 ? (
                <Card variant="surface" className="text-center py-12 px-4 space-y-3 shadow-subtle border-border">
                  <div className="w-12 h-12 mx-auto rounded-2xl bg-success/10 text-success border border-success/20 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <h3 className="font-heading font-semibold text-base text-midnight">
                    No Pending Registration Requests
                  </h3>
                  <p className="text-xs text-text-secondary max-w-sm mx-auto leading-relaxed">
                    All employee onboarding applications have been reviewed. When an invited employee registers with their pre-issued ID, their request will appear here for review.
                  </p>
                </Card>
              ) : (
                <div className="space-y-3">
                  {pendingRequests.map((req) => (
                    <Card
                      key={req.employee_id}
                      variant="surface"
                      className="p-5 sm:p-6 border-amber-200/90 shadow-subtle hover:border-amber-300 transition-all flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                    >
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2.5">
                          <span className="font-mono font-medium text-sm text-midnight">
                            {req.employee_id}
                          </span>
                          {renderStatusBadge(req.status)}
                          <span className="text-[11px] font-mono text-text-muted">
                            Registered: {req.registered_at ? new Date(req.registered_at).toLocaleDateString() : "Pending"}
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-secondary">
                          <span className="font-medium text-midnight">
                            {req.full_name || "Name not provided"}
                          </span>
                          <span>•</span>
                          <span className="font-mono text-text-primary">
                            {req.work_email}
                          </span>
                          <span>•</span>
                          <span>
                            Department: {req.department || "Customer Success"}
                          </span>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center gap-2 pt-2 lg:pt-0 border-t lg:border-t-0 border-border">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Eye}
                          onClick={() => setInspectingEmployee(req)}
                          className="text-xs text-text-secondary hover:text-midnight"
                        >
                          Details
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          icon={X}
                          onClick={() => {
                            setRejectingEmployee(req);
                            setRejectionReason("");
                            setRejectionError(null);
                          }}
                          className="text-xs font-medium"
                        >
                          Reject
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          icon={Check}
                          onClick={() => {
                            setApprovingEmployee(req);
                            setApprovalNotes("");
                          }}
                          className="text-xs font-medium bg-emerald-600 hover:bg-emerald-700 shadow-subtle text-white"
                        >
                          Approve
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ================================================================ */}
          {/* TAB 3: EMPLOYEE DIRECTORY                                        */}
          {/* ================================================================ */}
          {activeTab === "directory" && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h1 className="font-heading font-semibold text-2xl sm:text-3xl text-midnight tracking-tight">
                    Employee Directory
                  </h1>
                  <p className="text-xs text-text-secondary mt-1">
                    Complete persistent employee registry with status filtering, keyword search, and account audit details.
                  </p>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  icon={UserPlus}
                  onClick={() => setIsInviteModalOpen(true)}
                  className="text-xs font-medium shadow-subtle"
                >
                  Invite Employee
                </Button>
              </div>

              {/* Filter & Search Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 sm:p-4 bg-surface border border-border rounded-2xl shadow-subtle">
                {/* Search Bar */}
                <div className="relative flex-grow max-w-md">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
                    <Search className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={directorySearchQuery}
                    onChange={(e) => {
                      setDirectorySearchQuery(e.target.value);
                      setDirectoryPage(0);
                    }}
                    placeholder="Search by ID, email, or name..."
                    className="w-full pl-9 pr-3.5 py-2.5 text-xs rounded-xl border border-border bg-bg text-text-primary focus:outline-none focus:ring-2 focus:ring-electric"
                  />
                </div>

                {/* Status Filter */}
                <div className="flex items-center gap-2">
                  <Filter className="w-3.5 h-3.5 text-text-muted shrink-0" />
                  <span className="text-xs font-medium text-text-secondary">Status:</span>
                  <select
                    value={directoryStatusFilter}
                    onChange={(e) => {
                      setDirectoryStatusFilter(e.target.value);
                      setDirectoryPage(0);
                    }}
                    className="text-xs py-2.5 px-3.5 rounded-xl border border-border bg-bg text-midnight font-medium focus:outline-none focus:ring-2 focus:ring-electric"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="APPROVED">Approved</option>
                    <option value="PENDING">Pending</option>
                    <option value="INVITED">Invited</option>
                    <option value="REJECTED">Rejected</option>
                    <option value="SUSPENDED">Suspended</option>
                  </select>
                </div>
              </div>

              {/* Directory Table */}
              <div className="bg-surface border border-border rounded-2xl shadow-subtle overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/80 border-b border-border text-text-muted font-mono uppercase text-[10px] tracking-wider">
                      <tr>
                        <th className="py-3 px-4.5">Employee ID</th>
                        <th className="py-3 px-4.5">Name & Email</th>
                        <th className="py-3 px-4.5">Department</th>
                        <th className="py-3 px-4.5">Status</th>
                        <th className="py-3 px-4.5">Created / Reg.</th>
                        <th className="py-3 px-4.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {isDirectoryLoading ? (
                        <tr>
                          <td colSpan="6" className="py-8 text-center text-text-muted">
                            <span className="inline-flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin text-electric" /> Loading employee directory...
                            </span>
                          </td>
                        </tr>
                      ) : directoryEmployees.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="py-8 text-center text-text-muted">
                            No employee records matched your search or status filter.
                          </td>
                        </tr>
                      ) : (
                        directoryEmployees.map((emp) => (
                          <tr key={emp.employee_id} className="hover:bg-slate-50/50 transition-colors">
                            <td className="py-3.5 px-4.5 font-mono font-medium text-midnight">
                              {emp.employee_id}
                            </td>
                            <td className="py-3.5 px-4.5">
                              <div className="font-medium text-midnight">{emp.full_name || "—"}</div>
                              <div className="font-mono text-text-secondary text-[11px]">{emp.work_email}</div>
                            </td>
                            <td className="py-3.5 px-4.5 text-text-secondary">
                              {emp.department || "Customer Success"}
                            </td>
                            <td className="py-3.5 px-4.5">
                              {renderStatusBadge(emp.status)}
                            </td>
                            <td className="py-3.5 px-4.5 text-text-muted font-mono text-[11px]">
                              {emp.registered_at
                                ? new Date(emp.registered_at).toLocaleDateString()
                                : emp.created_at
                                  ? new Date(emp.created_at).toLocaleDateString()
                                  : "—"}
                            </td>
                            <td className="py-3.5 px-4.5 text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                icon={Eye}
                                onClick={() => setInspectingEmployee(emp)}
                                className="text-xs text-text-secondary hover:text-midnight"
                              >
                                Details
                              </Button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Footer */}
                <div className="py-3 px-4.5 border-t border-border bg-slate-50/50 flex items-center justify-between text-xs text-text-secondary">
                  <span>
                    Showing {directoryEmployees.length} record{directoryEmployees.length !== 1 ? "s" : ""}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      icon={ChevronLeft}
                      disabled={directoryPage === 0}
                      onClick={() => setDirectoryPage((p) => Math.max(0, p - 1))}
                      className="px-2.5 py-1 text-xs"
                    >
                      Previous
                    </Button>
                    <span className="font-mono text-[11px]">Page {directoryPage + 1}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      icon={ChevronRight}
                      iconPosition="right"
                      disabled={directoryEmployees.length < PAGE_SIZE}
                      onClick={() => setDirectoryPage((p) => p + 1)}
                      className="px-2.5 py-1 text-xs"
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ==================================================================== */}
      {/* MODAL 1: INSPECT EMPLOYEE DETAILS                                     */}
      {/* ==================================================================== */}
      {inspectingEmployee && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl shadow-elevated max-w-lg w-full p-6 sm:p-7 space-y-5 sm:space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  EMPLOYEE REGISTRY PROFILE
                </span>
                <h3 className="font-heading font-semibold text-xl text-midnight flex items-center gap-2.5 mt-0.5">
                  <span className="font-mono">{inspectingEmployee.employee_id}</span>
                  {renderStatusBadge(inspectingEmployee.status)}
                </h3>
              </div>
              <button
                onClick={() => setInspectingEmployee(null)}
                className="p-1 rounded-lg text-text-muted hover:text-midnight hover:bg-slate-100"
                aria-label="Close dialog"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-border space-y-2">
                <div className="flex justify-between">
                  <span className="text-text-muted">Work Email:</span>
                  <span className="font-mono font-medium text-midnight">{inspectingEmployee.work_email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Full Name:</span>
                  <span className="font-medium text-midnight">{inspectingEmployee.full_name || "Not provided"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Department:</span>
                  <span className="text-midnight">{inspectingEmployee.department || "Customer Success"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Supabase UUID:</span>
                  <span className="font-mono text-[10.5px] text-text-secondary truncate max-w-[200px]">
                    {inspectingEmployee.supabase_user_id || "Unbound (Awaiting Registration)"}
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-border space-y-2 text-[11.5px]">
                <div className="flex justify-between">
                  <span className="text-text-muted">Created Timestamp:</span>
                  <span className="font-mono">{inspectingEmployee.created_at || "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Registered Timestamp:</span>
                  <span className="font-mono">{inspectingEmployee.registered_at || "—"}</span>
                </div>
                {inspectingEmployee.approved_at && (
                  <div className="flex justify-between text-emerald-800">
                    <span>Approved Timestamp:</span>
                    <span className="font-mono">{inspectingEmployee.approved_at}</span>
                  </div>
                )}
                {inspectingEmployee.approved_by && (
                  <div className="flex justify-between text-emerald-800">
                    <span>Approved By Admin UUID:</span>
                    <span className="font-mono text-[10px] truncate max-w-[180px]">{inspectingEmployee.approved_by}</span>
                  </div>
                )}
                {inspectingEmployee.rejection_reason && (
                  <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-800 space-y-1">
                    <span className="font-semibold block">Rejection Reason:</span>
                    <p className="leading-relaxed">{inspectingEmployee.rejection_reason}</p>
                  </div>
                )}
                {inspectingEmployee.notes && (
                  <div className="p-2.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 space-y-1">
                    <span className="font-semibold block">Notes:</span>
                    <p className="leading-relaxed">{inspectingEmployee.notes}</p>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setInspectingEmployee(null)}
                className="text-xs"
              >
                Close Profile
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 2: CONFIRM APPROVAL                                             */}
      {/* ==================================================================== */}
      {approvingEmployee && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl shadow-elevated max-w-md w-full p-6 sm:p-7 space-y-5 sm:space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center shrink-0">
                <UserCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-heading font-semibold text-lg text-midnight">
                  Confirm Employee Approval
                </h3>
                <p className="text-xs text-text-secondary">
                  Grant customer intelligence and retention portal access.
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-border text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-text-muted">Employee ID:</span>
                <span className="font-mono font-medium text-midnight">{approvingEmployee.employee_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Work Email:</span>
                <span className="font-mono text-midnight">{approvingEmployee.work_email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Full Name:</span>
                <span className="text-midnight">{approvingEmployee.full_name || "—"}</span>
              </div>
            </div>

            <div>
              <label htmlFor="approval-notes" className="block text-xs font-heading font-medium text-midnight mb-1">
                Administrative Approval Notes (Optional)
              </label>
              <textarea
                id="approval-notes"
                rows="2"
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder="e.g. Approved for Customer Retention Operations analyst role"
                className="w-full p-2.5 text-xs rounded-xl border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-electric"
              />
            </div>

            <div className="p-3 rounded-xl bg-emerald-50/80 border border-emerald-200 text-emerald-900 text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>
                Upon approval, this employee account status will be set to <strong className="font-mono">APPROVED</strong>, authorizing access to customer APIs and churn risk diagnostics.
              </span>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={isSubmittingApproval}
                onClick={() => setApprovingEmployee(null)}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={Check}
                loading={isSubmittingApproval}
                onClick={handleConfirmApproval}
                className="text-xs font-medium bg-emerald-600 hover:bg-emerald-700 text-white shadow-subtle"
              >
                Confirm Approval
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 3: REJECT WITH MANDATORY REASON                                 */}
      {/* ==================================================================== */}
      {rejectingEmployee && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl shadow-elevated max-w-md w-full p-6 sm:p-7 space-y-5 sm:space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-50 text-red-700 border border-red-200 flex items-center justify-center shrink-0">
                <UserX className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-heading font-semibold text-lg text-midnight">
                  Reject Employee Registration
                </h3>
                <p className="text-xs text-text-secondary">
                  A mandatory objective reason is required for administrative audit logs.
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-border text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-text-muted">Employee ID:</span>
                <span className="font-mono font-medium text-midnight">{rejectingEmployee.employee_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Work Email:</span>
                <span className="font-mono text-midnight">{rejectingEmployee.work_email}</span>
              </div>
            </div>

            {rejectionError && (
              <div className="p-2.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{rejectionError}</span>
              </div>
            )}

            <div>
              <label htmlFor="rejection-reason" className="block text-xs font-heading font-medium text-midnight mb-1">
                Rejection Reason (Mandatory) <span className="text-red-500">*</span>
              </label>
              <textarea
                id="rejection-reason"
                rows="3"
                value={rejectionReason}
                onChange={(e) => {
                  setRejectionReason(e.target.value);
                  if (rejectionError) setRejectionError(null);
                }}
                placeholder="e.g. Invalid organization credentials or mismatched department authorization"
                className="w-full p-2.5 text-xs rounded-xl border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-electric"
              />
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={isSubmittingRejection}
                onClick={() => setRejectingEmployee(null)}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                icon={UserX}
                loading={isSubmittingRejection}
                onClick={handleConfirmRejection}
                className="text-xs font-medium"
              >
                Confirm Rejection
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 4: PRE-AUTHORIZE / INVITE EMPLOYEE                              */}
      {/* ==================================================================== */}
      {isInviteModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl shadow-elevated max-w-lg w-full p-6 sm:p-7 space-y-5 sm:space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-electric bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full font-medium inline-block mb-1">
                  PRE-AUTHORIZATION WORKFLOW
                </span>
                <h3 className="font-heading font-semibold text-xl text-midnight">
                  Pre-Authorize Employee Invitation
                </h3>
                <p className="text-xs text-text-secondary mt-0.5">
                  Creates an authorized employee registry entry with status <strong className="font-mono font-medium">INVITED</strong>.
                </p>
              </div>
              <button
                onClick={() => setIsInviteModalOpen(false)}
                className="p-1 rounded-lg text-text-muted hover:text-midnight hover:bg-slate-100"
                aria-label="Close dialog"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {inviteErrors.submit && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{inviteErrors.submit}</span>
              </div>
            )}

            <form onSubmit={handleInviteSubmit} className="space-y-3.5 text-xs">
              <div>
                <label htmlFor="inv-emp-id" className="block font-heading font-medium text-midnight mb-1">
                  Employee ID <span className="text-red-500">*</span>
                </label>
                <input
                  id="inv-emp-id"
                  type="text"
                  value={inviteForm.employee_id}
                  onChange={(e) => setInviteForm({ ...inviteForm, employee_id: e.target.value })}
                  placeholder="EMP-2026-004"
                  className="w-full p-2.5 rounded-xl border border-border bg-surface uppercase font-mono focus:outline-none focus:ring-2 focus:ring-electric"
                />
                {inviteErrors.employee_id && (
                  <p className="text-red-600 text-[11px] mt-1">{inviteErrors.employee_id}</p>
                )}
              </div>

              <div>
                <label htmlFor="inv-email" className="block font-heading font-medium text-midnight mb-1">
                  Enterprise Work Email <span className="text-red-500">*</span>
                </label>
                <input
                  id="inv-email"
                  type="email"
                  value={inviteForm.work_email}
                  onChange={(e) => setInviteForm({ ...inviteForm, work_email: e.target.value })}
                  placeholder="analyst.ops@ecommerce.in"
                  className="w-full p-2.5 rounded-xl border border-border bg-surface focus:outline-none focus:ring-2 focus:ring-electric"
                />
                {inviteErrors.work_email && (
                  <p className="text-red-600 text-[11px] mt-1">{inviteErrors.work_email}</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="inv-name" className="block font-heading font-medium text-midnight mb-1">
                    Full Name (Optional)
                  </label>
                  <input
                    id="inv-name"
                    type="text"
                    value={inviteForm.full_name}
                    onChange={(e) => setInviteForm({ ...inviteForm, full_name: e.target.value })}
                    placeholder="e.g. Priya Sharma"
                    className="w-full p-2.5 rounded-xl border border-border bg-surface focus:outline-none focus:ring-2 focus:ring-electric"
                  />
                </div>
                <div>
                  <label htmlFor="inv-dept" className="block font-heading font-medium text-midnight mb-1">
                    Department
                  </label>
                  <input
                    id="inv-dept"
                    type="text"
                    value={inviteForm.department}
                    onChange={(e) => setInviteForm({ ...inviteForm, department: e.target.value })}
                    placeholder="Customer Success"
                    className="w-full p-2.5 rounded-xl border border-border bg-surface focus:outline-none focus:ring-2 focus:ring-electric"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="inv-notes" className="block font-heading font-medium text-midnight mb-1">
                  Invitation Notes (Optional)
                </label>
                <input
                  id="inv-notes"
                  type="text"
                  value={inviteForm.notes}
                  onChange={(e) => setInviteForm({ ...inviteForm, notes: e.target.value })}
                  placeholder="e.g. Authorized by Ops Director for Q4 retention pilot"
                  className="w-full p-2.5 rounded-xl border border-border bg-surface focus:outline-none focus:ring-2 focus:ring-electric"
                />
              </div>

              <div className="p-3 rounded-xl bg-blue-50/60 border border-blue-200/80 text-blue-900 text-[11px] flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-electric shrink-0 mt-0.5" />
                <span>
                  The employee can now register at <strong className="font-mono">/employee/login</strong> using this pre-issued Employee ID and matching work email.
                </span>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={isSubmittingInvite}
                  onClick={() => setIsInviteModalOpen(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  icon={UserPlus}
                  loading={isSubmittingInvite}
                  className="text-xs font-medium shadow-subtle"
                >
                  Create Invitation
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
