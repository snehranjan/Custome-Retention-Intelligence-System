/**
 * RetainIQ Customer Retention Intelligence System
 * Employee Portal Dashboard Shell (Phase 8.4.7)
 *
 * Requirements:
 * - Enterprise aesthetic with RetainIQ design tokens (Midnight Navy, Electric Blue, Cyan, Slate 50).
 * - Real backend verification via apiClient.employee.getProfile():
 *   - Enforces ADMIN-CONTROLLED EMPLOYEE ACCOUNTS policy (APPROVED accounts only).
 *   - Retrieves verified identity (employee_id, full_name, work_email, department, status, approved_at).
 * - Top Navigation Bar: RetainIQ branding, employee verified profile chip, system connectivity indicator, and secure sign out.
 * - Sidebar Navigation establishing Phase 8.4.8 structure:
 *   - Overview (active working workstation)
 *   - Customer Directory (Phase 8.4.8 roadmap placeholder)
 *   - Churn Predictions (Phase 8.4.8 roadmap placeholder)
 *   - Customer Segments (Phase 8.4.8 roadmap placeholder)
 *   - Retention Actions (Phase 8.4.8 roadmap placeholder)
 *   - Analytics & Reports (Phase 8.4.8 roadmap placeholder)
 * - Safe status screens for non-approved states:
 *   - PENDING (awaiting administrator review)
 *   - REJECTED (access not approved)
 *   - SUSPENDED (account suspended)
 *   - INVITED (registration incomplete)
 *   - UNAUTHENTICATED (session expired / login required)
 * - Responsive at 1440px, 1024px, 768px, 390px.
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  LayoutDashboard,
  Users,
  BrainCircuit,
  PieChart,
  Zap,
  BarChart3,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  Clock,
  LogOut,
  ArrowLeft,
  ArrowRight,
  Lock,
  Building2,
  IdCard,
  Mail,
  FileText,
  Sparkles,
  RefreshCw,
  Loader2,
  ChevronRight,
  Menu,
  X,
  Database,
  Cpu,
  Layers,
  Activity,
  UserX,
  ExternalLink,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { apiClient } from "../lib/apiClient";
import { supabase } from "../lib/supabase";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { Container } from "../components/ui/Container";
import { ThemeToggle } from "../components/ui/ThemeToggle";

import { OverviewDashboard } from "../components/dashboard/OverviewDashboard";
import { CustomerExplorer } from "../components/dashboard/CustomerExplorer";
import { PredictionExplorer } from "../components/dashboard/PredictionExplorer";
import { SegmentationExplorer } from "../components/dashboard/SegmentationExplorer";
import { RecommendationCenter } from "../components/dashboard/RecommendationCenter";
import { AnalyticsPerformance } from "../components/dashboard/AnalyticsPerformance";

export function EmployeeDashboardPage({ onNavigate }) {
  const { session, user, isLoading: isAuthLoading } = useAuth();

  // Navigation & View State: 'overview' | 'customers' | 'predictions' | 'segments' | 'recommendations' | 'analytics'
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== "undefined") {
      const p = new URLSearchParams(window.location.search).get("tab");
      if (p && ["overview", "customers", "predictions", "segments", "recommendations", "analytics"].includes(p)) {
        return p;
      }
    }
    return "overview";
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [filterSegment, setFilterSegment] = useState("ALL");
  const [selectedCustomerIdForPrediction, setSelectedCustomerIdForPrediction] = useState("IND_CUST_10001");

  // Dynamic document title based on active module tab
  useEffect(() => {
    const tabTitles = {
      overview: "Overview | RetainIQ Employee Portal",
      customers: "Customer Explorer | RetainIQ",
      predictions: "Churn Prediction Explorer | RetainIQ",
      segments: "Customer Segmentation Explorer | RetainIQ",
      recommendations: "Retention Recommendations | RetainIQ",
      analytics: "Model Performance & Analytics | RetainIQ",
    };
    document.title = tabTitles[activeTab] || "Employee Portal | RetainIQ";
  }, [activeTab]);

  // Handle Escape key to close mobile menu
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileMenuOpen]);

  // Employee Verification & Profile State
  const [isVerifying, setIsVerifying] = useState(true);
  const [isAdminUser, setIsAdminUser] = useState(false);
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [authError, setAuthError] = useState(null); // { status: number, code: string, message: string }
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Backend Verification Effect
  const verifyEmployeeAccess = useCallback(async () => {
    if (!session?.access_token) {
      setIsVerifying(false);
      return;
    }

    setIsVerifying(true);
    setAuthError(null);
    setIsAdminUser(false);

    try {
      const res = await apiClient.employee.getProfile();
      if (res?.success && res?.data) {
        setEmployeeProfile(res.data);
      } else {
        setAuthError({
          status: 500,
          code: "INVALID_RESPONSE",
          message: "Unexpected response format received from employee profile endpoint.",
        });
      }
    } catch (err) {
      const status = err.status || 500;
      const message =
        err.data?.error?.message ||
        err.message ||
        "Employee access authorization could not be verified.";
      const code = err.data?.error?.code || (status === 403 ? "FORBIDDEN" : "AUTH_ERROR");

      // Check if authenticated account is an Administrator who navigated to employee portal
      if (status === 403) {
        try {
          const adminCheck = await apiClient.admin.getProfile();
          if (adminCheck?.success && adminCheck?.data?.is_admin) {
            setIsAdminUser(true);
            setAuthError({
              status: 403,
              code: "ADMIN_ACCOUNT",
              message: "Account possesses verified system administrator privileges.",
            });
            return;
          }
        } catch {
          // Non-admin account, proceed with standard employee error handling
        }
      }

      setAuthError({ status, code, message });
    } finally {
      setIsVerifying(false);
      setIsRefreshing(false);
    }
  }, [session]);

  useEffect(() => {
    verifyEmployeeAccess();
  }, [verifyEmployeeAccess]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    verifyEmployeeAccess();
  };

  const handleSignOut = async () => {
    try {
      if (supabase) {
        await supabase.auth.signOut();
      }
    } catch (err) {
      console.error("[RetainIQ Employee Portal] Sign out error:", err);
    } finally {
      setEmployeeProfile(null);
      if (onNavigate) {
        onNavigate("/employee/login");
      } else {
        window.location.pathname = "/employee/login";
      }
    }
  };

  const handleNavigate = (path) => {
    if (onNavigate) {
      onNavigate(path);
    } else {
      window.location.pathname = path;
    }
  };

  // ---------------------------------------------------------------------------
  // 1. Loading State (Cryptographic Verification in Progress)
  // ---------------------------------------------------------------------------
  if (isAuthLoading || isVerifying) {
    return (
      <div className="min-h-screen bg-bg text-text-primary flex flex-col justify-center items-center p-4">
        <div className="w-full max-w-md bg-surface border border-border rounded-2xl p-8 shadow-elevated text-center space-y-4">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-electric/10 text-electric border border-electric/20 flex items-center justify-center">
            <Loader2 className="w-7 h-7 animate-spin" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-electric/10 text-electric border border-electric/20 inline-block mb-2">
              SECURITY AUDIT IN PROGRESS
            </span>
            <h2 className="font-heading text-xl font-bold text-midnight tracking-tight">
              Verifying Employee Clearance
            </h2>
            <p className="text-xs text-text-secondary mt-1 leading-relaxed">
              Cryptographically evaluating Supabase session against the server-side employee registry.
            </p>
          </div>
          <div className="p-3 bg-bg border border-border/80 rounded-xl text-[11px] font-mono text-text-muted text-left space-y-1">
            <div className="flex justify-between">
              <span>Token Verification:</span>
              <span className="text-electric font-semibold">ES256 JWKS</span>
            </div>
            <div className="flex justify-between">
              <span>Authorization Policy:</span>
              <span className="text-midnight font-semibold">ADMIN-CONTROLLED</span>
            </div>
            <div className="flex justify-between">
              <span>Required Status:</span>
              <span className="text-success font-semibold">APPROVED</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 2. Unauthenticated State (No Active Session)
  // ---------------------------------------------------------------------------
  if (!session || !user) {
    return (
      <div className="min-h-screen bg-bg text-text-primary flex flex-col justify-center items-center p-4">
        <div className="w-full max-w-md bg-surface border border-border rounded-2xl p-8 shadow-elevated text-center space-y-5">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center">
            <Lock className="w-7 h-7" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-amber-100 text-amber-800 border border-amber-200 inline-block mb-2">
              SESSION REQUIRED
            </span>
            <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
              Authentication Required
            </h2>
            <p className="text-xs text-text-secondary mt-1 leading-relaxed">
              The RetainIQ Employee Portal is protected by enterprise authentication. Please sign in with your approved employee credentials.
            </p>
          </div>
          <div className="space-y-2.5 pt-2">
            <Button
              variant="primary"
              size="md"
              onClick={() => handleNavigate("/employee/login")}
              icon={ArrowRight}
              className="w-full justify-center text-xs font-semibold"
            >
              Go to Employee Sign In
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleNavigate("/")}
              icon={ArrowLeft}
              className="w-full justify-center text-xs text-text-secondary"
            >
              Return to Public Showcase
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 3. Authorization Error / Non-Approved Status Screens
  // ---------------------------------------------------------------------------
  if (authError) {
    const errorMsg = (authError.message || "").toLowerCase();
    const isPending = errorMsg.includes("awaiting administrator approval") || errorMsg.includes("pending");
    const isRejected = errorMsg.includes("rejected by administrator") || errorMsg.includes("rejected");
    const isSuspended = errorMsg.includes("suspended by administrator") || errorMsg.includes("suspended");
    const isInvited = errorMsg.includes("not completed") || errorMsg.includes("registration");
    const is404 = authError.status === 404;

    return (
      <div className="min-h-screen bg-bg text-text-primary flex flex-col justify-center items-center p-4">
        <div className="w-full max-w-lg bg-surface border border-border rounded-2xl p-8 shadow-elevated text-center space-y-6">
          {isAdminUser ? (
            /* 3-ADMIN: ADMINISTRATOR ACCOUNT DETECTED SCREEN */
            <>
              <div className="w-16 h-16 mx-auto rounded-2xl bg-midnight text-cyan border border-cyan/30 flex items-center justify-center">
                <ShieldCheck className="w-8 h-8 text-cyan" />
              </div>
              <div className="space-y-1.5">
                <span className="px-3 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-cyan/10 text-cyan-900 border border-cyan/30 inline-block">
                  ADMINISTRATOR PRIVILEGES VERIFIED
                </span>
                <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
                  Administrator Account Detected
                </h2>
                <p className="text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
                  You are signed in with system administrator privileges ({user.email}). The Employee Dashboard is designed for operational retention analysts. You can manage employee registrations, send invitations, and view registry stats in the Administrator Portal.
                </p>
              </div>
            </>
          ) : is404 ? (
            /* 3-404: SERVICE UNAVAILABLE SCREEN */
            <>
              <div className="w-16 h-16 mx-auto rounded-2xl bg-red-50 text-red-600 border border-red-200 flex items-center justify-center">
                <AlertCircle className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <span className="px-3 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-red-100 text-red-900 border border-red-200 inline-block">
                  SERVICE UNAVAILABLE (404)
                </span>
                <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
                  Employee Service Endpoint Not Found
                </h2>
                <p className="text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
                  The backend employee service endpoint could not be resolved. Please verify that the FastAPI backend server is running on http://127.0.0.1:8000.
                </p>
              </div>
            </>
          ) : isPending ? (
            /* 3A: PENDING STATUS SCREEN */
            <>
              <div className="w-16 h-16 mx-auto rounded-2xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center">
                <Clock className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <span className="px-3 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-amber-100 text-amber-900 border border-amber-200 inline-block">
                  REGISTRATION STATUS: PENDING
                </span>
                <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
                  Registration Under Administrator Review
                </h2>
                <p className="text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
                  Your employee account registration has been submitted and is currently in the administrator review queue. Once an administrator approves your profile, full access to this portal will unlock immediately.
                </p>
              </div>
            </>
          ) : isRejected ? (
            /* 3B: REJECTED STATUS SCREEN */
            <>
              <div className="w-16 h-16 mx-auto rounded-2xl bg-red-50 text-red-600 border border-red-200 flex items-center justify-center">
                <UserX className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <span className="px-3 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-red-100 text-red-900 border border-red-200 inline-block">
                  REGISTRATION STATUS: REJECTED
                </span>
                <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
                  Access Not Approved
                </h2>
                <p className="text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
                  Your registration request was reviewed and not approved by an administrator. Please reach out to your department supervisor or system administrator for assistance.
                </p>
              </div>
            </>
          ) : isSuspended ? (
            /* 3C: SUSPENDED STATUS SCREEN */
            <>
              <div className="w-16 h-16 mx-auto rounded-2xl bg-slate-100 text-slate-700 border border-slate-300 flex items-center justify-center">
                <ShieldAlert className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <span className="px-3 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-slate-200 text-slate-800 border border-slate-300 inline-block">
                  ACCOUNT STATUS: SUSPENDED
                </span>
                <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
                  Account Access Suspended
                </h2>
                <p className="text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
                  This employee account has been suspended by an administrator. Portal features and customer data access are temporarily disabled.
                </p>
              </div>
            </>
          ) : isInvited ? (
            /* 3D: INVITED STATUS SCREEN */
            <>
              <div className="w-16 h-16 mx-auto rounded-2xl bg-cyan/10 text-cyan border border-cyan/30 flex items-center justify-center">
                <IdCard className="w-8 h-8 text-midnight" />
              </div>
              <div className="space-y-1.5">
                <span className="px-3 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-cyan/10 text-cyan-900 border border-cyan/30 inline-block">
                  INVITATION UNLINKED
                </span>
                <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
                  Registration Incomplete
                </h2>
                <p className="text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
                  Your administrator-issued Employee ID has been pre-authorized, but registration linking has not been completed. Please complete registration on the employee portal sign-in page.
                </p>
              </div>
            </>
          ) : (
            /* 3E: GENERAL ACCESS RESTRICTED SCREEN */
            <>
              <div className="w-16 h-16 mx-auto rounded-2xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center">
                <ShieldAlert className="w-8 h-8" />
              </div>
              <div className="space-y-1.5">
                <span className="px-3 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full bg-amber-100 text-amber-900 border border-amber-200 inline-block">
                  AUTHORIZATION RESTRICTED
                </span>
                <h2 className="font-heading text-2xl font-bold text-midnight tracking-tight">
                  Employee Clearance Required
                </h2>
                <p className="text-xs text-text-secondary leading-relaxed max-w-md mx-auto">
                  {authError.message || "Your identity is authenticated, but does not have verified employee clearance."}
                </p>
              </div>
            </>
          )}

          {/* Details Card */}
          <div className="p-4 bg-bg border border-border rounded-xl text-xs space-y-2 text-left">
            <div className="flex justify-between items-center text-text-muted">
              <span>Authenticated Email:</span>
              <span className="font-mono font-semibold text-midnight truncate max-w-[240px]">
                {user.email || "No email claim"}
              </span>
            </div>
            <div className="flex justify-between items-center text-text-muted">
              <span>Account Subject ID:</span>
              <span className="font-mono text-text-secondary text-[11px] truncate max-w-[240px]">
                {user.id}
              </span>
            </div>
            <div className="flex justify-between items-center text-text-muted">
              <span>Security Role / Policy:</span>
              <span className="font-mono text-[11px] text-electric font-semibold">
                {isAdminUser ? "SYSTEM ADMINISTRATOR" : "ADMIN-CONTROLLED EMPLOYEE ACCOUNTS"}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-2.5 pt-2">
            {isAdminUser ? (
              <Button
                variant="primary"
                size="md"
                onClick={() => handleNavigate("/admin")}
                icon={ArrowRight}
                className="w-full justify-center text-xs font-semibold"
              >
                Launch Administrator Portal (/admin)
              </Button>
            ) : (
              <Button
                variant="outline"
                size="md"
                onClick={handleRefresh}
                icon={RefreshCw}
                disabled={isRefreshing}
                className="w-full justify-center text-xs font-semibold"
              >
                {isRefreshing ? "Checking Status..." : "Refresh Authorization Status"}
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSignOut}
              icon={LogOut}
              className="w-full justify-center text-xs text-text-secondary hover:text-midnight"
            >
              Sign Out & Switch Account
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleNavigate("/")}
              icon={ArrowLeft}
              className="w-full justify-center text-xs text-text-muted"
            >
              Return to Public Showcase
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 4. Authorized Employee Shell (APPROVED Status)
  // ---------------------------------------------------------------------------
  const empName = employeeProfile?.full_name || "Authorized Employee";
  const empId = employeeProfile?.employee_id || "EMP-2026-001";
  const empEmail = employeeProfile?.work_email || user.email || "";
  const empDept = employeeProfile?.department || "Customer Retention Operations";

  const navigationItems = [
    {
      id: "overview",
      label: "Workstation Overview",
      icon: LayoutDashboard,
      badge: "Live",
      description: "Employee workspace & system status",
    },
    {
      id: "customers",
      label: "Customer Directory",
      icon: Users,
      badge: "7,000",
      description: "Customer cohorts, profiles & history",
    },
    {
      id: "predictions",
      label: "Churn Predictions",
      icon: BrainCircuit,
      badge: "τ=0.50",
      description: "Batch & real-time inference (τ=0.50)",
    },
    {
      id: "segments",
      label: "Customer Segments",
      icon: PieChart,
      badge: "K=5",
      description: "5 RFM persona cluster mappings",
    },
    {
      id: "recommendations",
      label: "Retention Actions",
      icon: Zap,
      badge: "16.5k",
      description: "Prescriptive intervention strategies",
    },
    {
      id: "analytics",
      label: "Analytics & Reports",
      icon: BarChart3,
      badge: "N=1,500",
      description: "Model metrics & cohort health trends",
    },
  ];

  return (
    <div className="min-h-screen bg-bg text-text-primary flex flex-col selection:bg-electric selection:text-white">
      {/* ===================================================================== */}
      {/* TOP NAVIGATION BAR                                                   */}
      {/* ===================================================================== */}
      <header className="sticky top-0 z-40 border-b border-border bg-surface/95 backdrop-blur-md">
        <Container size="full" className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left: Branding & Portal Badge */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  setActiveTab("overview");
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-electric rounded-lg"
                aria-label="RetainIQ Employee Dashboard"
              >
                <div className="w-9 h-9 rounded-lg bg-midnight flex items-center justify-center border border-slate-800 group-hover:border-slate-700 transition-colors">
                  <svg
                    className="w-4.5 h-4.5 text-white"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M4 12v-3a8 8 0 0 1 16 0v3" />
                    <path d="M9 18l3 3 3-3" />
                    <circle cx="12" cy="12" r="3" fill="#0052CC" stroke="none" />
                  </svg>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-heading font-semibold text-lg text-midnight tracking-tight">
                    Retain<span className="text-electric">IQ</span>
                  </span>
                  <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-mono font-medium tracking-wide uppercase rounded bg-slate-100 text-text-secondary border border-slate-200">
                    EMPLOYEE PORTAL
                  </span>
                </div>
              </button>
            </div>

            {/* Right: Employee Profile Chip & Actions */}
            <div className="flex items-center gap-3 sm:gap-4">
              {/* System Connectivity Indicator (Desktop) */}
              <div className="hidden lg:flex items-center gap-2 px-3 py-1 bg-surface border border-border rounded-lg text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-600" />
                <span className="font-mono text-[11px] text-text-secondary">
                  FastAPI REST: <strong className="text-midnight font-semibold">Online</strong> • ES256 Verified
                </span>
              </div>

              {/* Employee Identity Pill */}
              <div className="flex items-center gap-2.5 px-3 py-1.5 bg-surface border border-border rounded-lg">
                <div className="w-7 h-7 rounded-md bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center font-semibold text-xs">
                  {empName.charAt(0).toUpperCase()}
                </div>
                <div className="flex flex-col text-left">
                  <div className="flex items-center gap-1.5">
                    <span className="font-heading font-semibold text-xs text-midnight leading-none">
                      {empName}
                    </span>
                    <span className="hidden sm:inline-block px-1.5 py-0.2 text-[9px] font-mono font-medium rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      APPROVED
                    </span>
                  </div>
                  <span className="text-[10px] text-text-muted font-mono leading-tight">
                    {empId} • {empDept}
                  </span>
                </div>
              </div>

              {/* Theme Toggle */}
              <ThemeToggle size="sm" />

              {/* Sign Out Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSignOut}
                icon={LogOut}
                className="text-text-secondary hover:text-midnight text-xs"
                title="Sign out of employee session"
              >
                <span className="hidden sm:inline">Sign Out</span>
              </Button>

              {/* Mobile Menu Toggle */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 text-text-secondary hover:text-midnight rounded-lg hover:bg-slate-100"
                aria-label="Toggle mobile navigation menu"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </Container>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <>
            <div 
              className="md:hidden fixed inset-0 top-16 bg-midnight/40 backdrop-blur-xs z-30"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="md:hidden relative z-40 border-t border-border bg-surface px-4 py-3 space-y-1 shadow-card animate-in slide-in-from-top-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? "bg-slate-100 text-electric font-semibold"
                        : "text-text-secondary hover:text-midnight hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                    </div>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        isActive
                          ? "bg-electric text-white"
                          : "bg-slate-100 text-text-muted border border-border"
                      }`}
                    >
                      {item.badge}
                    </span>
                  </button>
                );
              })}

              {/* Mobile Drawer Theme Toggle */}
              <div className="pt-2 mt-2 border-t border-border flex items-center justify-between px-3 py-1">
                <span className="text-xs font-mono text-text-muted">Appearance Theme</span>
                <ThemeToggle variant="pill" size="sm" />
              </div>
            </div>
          </>
        )}
      </header>

      {/* ===================================================================== */}
      {/* MAIN LAYOUT: SIDEBAR + CONTENT WORKSPACE                              */}
      {/* ===================================================================== */}
      <div className="flex-grow flex">
        {/* Desktop Sidebar Navigation */}
        <aside className="hidden md:flex flex-col w-64 lg:w-72 border-r border-border bg-surface shrink-0 p-4 space-y-5">
          {/* Employee Workspace Header Card */}
          <div className="p-3.5 bg-bg border border-border rounded-xl space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                WORKSPACE CONTEXT
              </span>
              <span className="w-2 h-2 rounded-full bg-emerald-600" />
            </div>
            <div className="font-heading font-semibold text-xs text-midnight">
              Customer Retention Operations
            </div>
            <div className="text-[11px] text-text-secondary font-mono leading-relaxed">
              Cleared for live churn scoring & prescriptive intervention review.
            </div>
          </div>

          {/* Navigation Links */}
          <div className="space-y-1">
            <span className="px-2 text-[10px] font-mono uppercase tracking-wider text-text-muted font-semibold block mb-1.5">
              SYSTEM MODULES
            </span>
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-slate-100 text-electric font-semibold"
                      : "text-text-secondary hover:text-midnight hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-electric" : "text-text-muted"
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                      isActive
                        ? "bg-electric text-white"
                        : "bg-slate-100 text-text-muted border border-border"
                    }`}
                  >
                    {item.badge}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Quick System Environment Summary in Sidebar */}
          <div className="mt-auto p-4 bg-bg border border-border rounded-xl space-y-2.5 text-xs text-text-secondary font-mono">
            <div className="flex items-center justify-between text-midnight font-semibold">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-text-secondary" /> Model Pipeline
              </span>
              <span>Config D</span>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span>Decision Cutoff:</span>
                <span className="text-midnight font-semibold">τ = 0.50</span>
              </div>
              <div className="flex justify-between">
                <span>Features:</span>
                <span className="text-midnight font-semibold">43 Variables</span>
              </div>
              <div className="flex justify-between">
                <span>Cluster Count:</span>
                <span className="text-midnight font-semibold">5 Personas</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Content Workspace */}
        <main className="flex-grow p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {activeTab === "overview" && (
            /* ================================================================ */
            /* TAB 1: WORKSTATION OVERVIEW                                     */
            /* ================================================================ */
            <div className="space-y-7 sm:space-y-8 max-w-6xl mx-auto">
              {/* Welcome Banner */}
              <div className="bg-midnight rounded-xl p-6 sm:p-8 text-white shadow-card border border-slate-800 space-y-5 sm:space-y-6">
                <div className="space-y-3.5">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="px-3 py-1 text-[10px] font-mono font-medium tracking-wide uppercase rounded bg-slate-800 text-slate-300 border border-slate-700">
                      EMPLOYEE PORTAL OPERATIONAL
                    </span>
                    <span className="px-3 py-1 text-[10px] font-mono font-medium tracking-wide uppercase rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5" /> VERIFIED CLEARANCE
                    </span>
                  </div>

                  <div>
                    <h1 className="font-heading text-2xl sm:text-3xl font-semibold tracking-tight text-white">
                      Welcome back, {empName}
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1.5 max-w-2xl leading-relaxed">
                      You are authenticated to the RetainIQ Customer Retention Intelligence System.
                      Explore customer cohorts, churn risk evaluations, and prescriptive retention actions.
                    </p>
                  </div>

                  {/* Profile Metadata Strip */}
                  <div className="pt-3 flex flex-wrap items-center gap-4 sm:gap-7 text-xs font-mono text-slate-400">
                    <div className="flex items-center gap-2">
                      <IdCard className="w-4 h-4 text-slate-400" />
                      <span>ID: <strong className="text-white">{empId}</strong></span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-slate-400" />
                      <span>Email: <strong className="text-white">{empEmail}</strong></span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-slate-400" />
                      <span>Dept: <strong className="text-white">{empDept}</strong></span>
                    </div>
                    {employeeProfile?.approved_at && (
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span>Approved: <strong className="text-white">{new Date(employeeProfile.approved_at).toLocaleDateString()}</strong></span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* System Connectivity & Integrity Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
                {/* Card 1: FastAPI REST Backend */}
                <div className="p-5 sm:p-5.5 bg-surface border border-border rounded-xl shadow-subtle space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-muted font-medium">REST API Gateway</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-600" />
                  </div>
                  <div className="font-heading font-semibold text-base text-midnight">
                    FastAPI Engine
                  </div>
                  <p className="text-xs text-text-secondary leading-normal">
                    HTTP REST service on port 8000 handling authentication, model inference, and customer data.
                  </p>
                  <div className="text-[11px] font-mono text-emerald-700 pt-1 font-medium flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Online & Verified
                  </div>
                </div>

                {/* Card 2: JWKS ES256 Session */}
                <div className="p-5 sm:p-5.5 bg-surface border border-border rounded-xl shadow-subtle space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-muted font-medium">Session Cryptography</span>
                    <span className="w-2 h-2 rounded-full bg-electric" />
                  </div>
                  <div className="font-heading font-semibold text-base text-midnight">
                    ES256 JWKS
                  </div>
                  <p className="text-xs text-text-secondary leading-normal">
                    Asymmetric public key token verification with live Supabase JWKS cache.
                  </p>
                  <div className="text-[11px] font-mono text-electric pt-1 font-medium flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" /> Active Secure Session
                  </div>
                </div>

                {/* Card 3: Machine Learning Model */}
                <div className="p-5 sm:p-5.5 bg-surface border border-border rounded-xl shadow-subtle space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-muted font-medium">Inference Engine</span>
                    <span className="w-2 h-2 rounded-full bg-slate-600" />
                  </div>
                  <div className="font-heading font-semibold text-base text-midnight">
                    Config D (RF)
                  </div>
                  <p className="text-xs text-text-secondary leading-normal">
                    Locked Random Forest classifier with 43 features and decision threshold τ = 0.50.
                  </p>
                  <div className="text-[11px] font-mono text-text-secondary pt-1 font-medium flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5" /> SHA-256 Audited
                  </div>
                </div>

                {/* Card 4: Customer Segmentation */}
                <div className="p-5 sm:p-5.5 bg-surface border border-border rounded-xl shadow-subtle space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-muted font-medium">Customer Personas</span>
                    <span className="w-2 h-2 rounded-full bg-slate-900" />
                  </div>
                  <div className="font-heading font-semibold text-base text-midnight">
                    K-Means RFM (K=5)
                  </div>
                  <p className="text-xs text-text-secondary leading-normal">
                    Persona clustering mapping 5 segments from Champions to At-Risk customers.
                  </p>
                  <div className="text-[11px] font-mono text-text-secondary pt-1 font-medium flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5" /> 5 Segment Profiles
                  </div>
                </div>
              </div>

              {/* Module 1: Overview Dashboard Component */}
              <OverviewDashboard onNavigateTab={(tab) => setActiveTab(tab)} />

              {/* Academic Capstone Compliance Banner */}
              <div className="p-4.5 sm:p-5 rounded-xl bg-bg border border-border text-xs text-text-secondary flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    RetainIQ Indian E-Commerce Customer Retention Intelligence System • Academic Milestone Phase 8.4.8 Complete
                  </span>
                </div>
                <div className="text-[11px] font-mono text-text-muted">
                  University Project Submission • 2026
                </div>
              </div>
              {/* Architecture Note: Transitioned from Phase 8.4.7 (SCHEDULED FOR PHASE 8.4.8 placeholders) to production modules with Return to Workstation Overview navigation. */}
            </div>
          )}

          {activeTab === "customers" && (
            <div className="max-w-6xl mx-auto">
              <CustomerExplorer
                initialSegment={filterSegment}
                onInspectPrediction={(id) => {
                  setSelectedCustomerIdForPrediction(id);
                  setActiveTab("predictions");
                }}
              />
            </div>
          )}

          {activeTab === "predictions" && (
            <div className="max-w-6xl mx-auto">
              <PredictionExplorer initialCustomerId={selectedCustomerIdForPrediction} />
            </div>
          )}

          {activeTab === "segments" && (
            <div className="max-w-6xl mx-auto">
              <SegmentationExplorer
                onFilterSegmentInCustomerExplorer={(clusterId) => {
                  setFilterSegment(String(clusterId));
                  setActiveTab("customers");
                }}
              />
            </div>
          )}

          {activeTab === "recommendations" && (
            <div className="max-w-6xl mx-auto">
              <RecommendationCenter
                onSelectCustomer={(customerId) => {
                  setSelectedCustomerIdForPrediction(customerId);
                  setActiveTab("predictions");
                }}
              />
            </div>
          )}

          {activeTab === "analytics" && (
            <div className="max-w-6xl mx-auto">
              <AnalyticsPerformance />
            </div>
          )}
        </main>
      </div>

      {/* ===================================================================== */}
      {/* FOOTER                                                                */}
      {/* ===================================================================== */}
      <footer className="border-t border-border bg-surface py-4">
        <Container size="full" className="px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-text-secondary">
          <p>© 2026 RetainIQ Intelligence System • BCA AI & ML Final Year Capstone</p>
          <div className="flex items-center gap-4 text-xs font-mono text-text-muted">
            <span className="text-success font-medium flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-success"></span>
              Phase 8.4.7 Employee Portal Shell Active
            </span>
            <span>React 19 • Vite 6 • Tailwind 3.4 • FastAPI REST</span>
          </div>
        </Container>
      </footer>
    </div>
  );
}
