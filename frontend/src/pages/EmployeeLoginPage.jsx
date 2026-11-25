/**
 * RetainIQ Customer Retention Intelligence System
 * Employee Authentication & Registration Page (Phase 8.4.5)
 *
 * Requirements:
 * - Enterprise aesthetic with RetainIQ tokens (Midnight Navy, Deep Navy, Electric Blue, Cyan, Slate 50).
 * - Two-tab interface: "Sign In" and "Register as an Employee".
 * - Full client-side validation (email format, whitespace trimming, required fields, password match).
 * - Show/Hide password toggle with accessible aria labels for all password fields.
 * - Loading, error, and success states with duplicate submission prevention.
 * - Employee ID validation via backend POST /api/v1/employee/register.
 * - Dedicated "Registration Submitted Successfully" pending approval view (NO dashboard access).
 * - Supabase signInWithPassword integration for login with sanitized user-friendly error messages.
 * - Post-login identity verification against GET /api/v1/auth/me via apiClient.
 * - Strict ADMIN-CONTROLLED EMPLOYEE ACCOUNTS policy (no open public signups, no client-side signUp()).
 */

import React, { useState, useEffect } from "react";
import {
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  ArrowLeft,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  LogOut,
  RefreshCw,
  Building2,
  IdCard,
  UserPlus,
  Clock,
} from "lucide-react";
import { supabase } from "../lib/supabase";
import { apiClient } from "../lib/apiClient";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/Button";
import { Container } from "../components/ui/Container";
import { ThemeToggle } from "../components/ui/ThemeToggle";

export function EmployeeLoginPage({ onNavigate }) {
  const { session, user, isLoading: isAuthLoading } = useAuth();

  // Active Tab: 'login' | 'register'
  const [activeTab, setActiveTab] = useState("login");

  // ---------------------------------------------------------------------------
  // Sign In Form State
  // ---------------------------------------------------------------------------
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ---------------------------------------------------------------------------
  // Registration Form State (Phase 8.4.5)
  // ---------------------------------------------------------------------------
  const [regEmployeeId, setRegEmployeeId] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirmPassword, setRegConfirmPassword] = useState("");
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [showRegConfirmPassword, setShowRegConfirmPassword] = useState(false);
  const [regValidationErrors, setRegValidationErrors] = useState({});
  const [regFormError, setRegFormError] = useState(null);
  const [isRegSubmitting, setIsRegSubmitting] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(null);

  // ---------------------------------------------------------------------------
  // Post-Login Backend Identity Verification State
  // ---------------------------------------------------------------------------
  const [verificationStatus, setVerificationStatus] = useState("idle"); // 'idle' | 'verifying' | 'verified' | 'failed'
  const [verifiedIdentity, setVerifiedIdentity] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [employeeStatusCategory, setEmployeeStatusCategory] = useState(null); // 'APPROVED' | 'PENDING' | 'REJECTED' | 'SUSPENDED' | 'INVITED' | 'UNREGISTERED'
  const [verificationError, setVerificationError] = useState(null);

  // Helper to check employee clearance
  const checkEmployeeClearance = (isMountedRef) => {
    return apiClient.employee
      .getProfile()
      .then((res) => {
        if (!isMountedRef.current) return;
        if (res?.success && res?.data && res.data.status === "APPROVED") {
          setEmployeeProfile(res.data);
          setEmployeeStatusCategory("APPROVED");
          setVerificationStatus("verified");
          // Automatically transition to employee dashboard for approved staff
          if (onNavigate) {
            onNavigate("/employee/dashboard");
          }
        } else {
          setEmployeeStatusCategory(res?.data?.status || "PENDING");
          setVerificationStatus("failed");
        }
      })
      .catch((err) => {
        if (!isMountedRef.current) return;
        setVerificationStatus("failed");
        if (err.status === 401) {
          setVerificationError("FastAPI rejected session token (401 Unauthorized). The token may be expired or invalid.");
          return;
        }
        if (err.status === 403) {
          const msg = (err.message || "").toLowerCase();
          if (msg.includes("awaiting") || msg.includes("pending")) {
            setEmployeeStatusCategory("PENDING");
          } else if (msg.includes("rejected")) {
            setEmployeeStatusCategory("REJECTED");
          } else if (msg.includes("suspended")) {
            setEmployeeStatusCategory("SUSPENDED");
          } else if (msg.includes("registration") || msg.includes("unbound")) {
            setEmployeeStatusCategory("INVITED");
          } else {
            setEmployeeStatusCategory("RESTRICTED");
          }
          setVerificationError(err.message || "Access denied by backend policy (403 Forbidden).");
          return;
        }
        setVerificationError(err.message || "Employee authorization verification failed.");
      });
  };

  // Trigger backend verification upon session creation or update
  useEffect(() => {
    const isMountedRef = { current: true };

    if (session?.access_token && user) {
      setVerificationStatus("verifying");
      setVerificationError(null);
      setIsAdmin(false);

      // Verify JWT claims first
      apiClient.auth
        .getProfile()
        .then((res) => {
          if (!isMountedRef.current) return;
          if (res?.success && res?.data) {
            setVerifiedIdentity(res.data);
          }
        })
        .catch(() => { });

      // First check if user is an Administrator via GET /api/v1/admin/me
      apiClient.admin
        .getProfile()
        .then((adminRes) => {
          if (!isMountedRef.current) return;
          if (adminRes?.success && adminRes?.data?.is_admin) {
            setIsAdmin(true);
            setVerificationStatus("verified");
            // Automatically transition administrator to admin portal
            if (onNavigate) {
              onNavigate("/admin");
            }
            return;
          }
          // Not an administrator, check employee registry clearance
          checkEmployeeClearance(isMountedRef);
        })
        .catch((err) => {
          if (!isMountedRef.current) return;
          // Only check employee clearance if explicitly forbidden (403: user is authenticated but not an admin)
          if (err?.status === 403 || err?.isForbiddenError) {
            checkEmployeeClearance(isMountedRef);
          } else {
            // Network connection failure (status 0), server error (500), or auth token rejection (401)
            setVerificationStatus("failed");
            setVerificationError(err?.message || "Failed to contact backend authorization service.");
          }
        });
    } else {
      setVerificationStatus("idle");
      setVerifiedIdentity(null);
      setIsAdmin(false);
      setEmployeeProfile(null);
      setEmployeeStatusCategory(null);
      setVerificationError(null);
    }

    return () => {
      isMountedRef.current = false;
    };
  }, [session, user, onNavigate]);

  // ---------------------------------------------------------------------------
  // Validation Handlers
  // ---------------------------------------------------------------------------
  const validateLoginForm = () => {
    const errors = {};
    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      errors.email = "Work email address is required.";
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(trimmedEmail)) {
        errors.email = "Please enter a valid work email address.";
      }
    }

    if (!password) {
      errors.password = "Password is required.";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateRegForm = () => {
    const errors = {};
    const cleanId = regEmployeeId.trim();
    const cleanEmail = regEmail.trim();

    if (!cleanId) {
      errors.employeeId = "Pre-issued Employee ID is required.";
    } else if (cleanId.length < 3) {
      errors.employeeId = "Employee ID must be at least 3 characters.";
    }

    if (!cleanEmail) {
      errors.email = "Work email address is required.";
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(cleanEmail)) {
        errors.email = "Please enter a valid work email address.";
      }
    }

    if (!regPassword) {
      errors.password = "Password is required.";
    } else if (regPassword.length < 8) {
      errors.password = "Password must be at least 8 characters long.";
    }

    if (!regConfirmPassword) {
      errors.confirmPassword = "Confirm password is required.";
    } else if (regPassword !== regConfirmPassword) {
      errors.confirmPassword = "Passwords do not match.";
    }

    setRegValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // ---------------------------------------------------------------------------
  // Sign In Handler
  // ---------------------------------------------------------------------------
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    setFormError(null);
    if (!validateLoginForm()) return;

    if (!supabase) {
      setFormError("Authentication service is unavailable. Please verify configuration.");
      return;
    }

    setIsSubmitting(true);
    const trimmedEmail = email.trim();

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: trimmedEmail,
        password: password,
      });

      if (error) {
        let userMessage = "Unable to sign in with provided credentials.";
        const rawMsg = error.message.toLowerCase();

        if (rawMsg.includes("invalid login credentials") || rawMsg.includes("invalid_grant")) {
          userMessage = "Invalid work email or password. Please verify your administrator-provisioned credentials.";
        } else if (rawMsg.includes("email not confirmed")) {
          userMessage = "Your work email address has not been confirmed. Please check your inbox or contact your RetainIQ administrator.";
        } else if (rawMsg.includes("too many requests") || rawMsg.includes("rate limit")) {
          userMessage = "Too many sign-in attempts. Please wait a few moments before trying again.";
        } else if (rawMsg.includes("network") || rawMsg.includes("fetch")) {
          userMessage = "Network connection error contacting authentication service.";
        }

        setFormError(userMessage);
      } else if (data?.session) {
        setPassword("");
      }
    } catch {
      setFormError("An unexpected error occurred during sign in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Registration Handler (Phase 8.4.5)
  // ---------------------------------------------------------------------------
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (isRegSubmitting) return;

    setRegFormError(null);
    if (!validateRegForm()) return;

    setIsRegSubmitting(true);
    const payload = {
      employee_id: regEmployeeId.trim().toUpperCase(),
      work_email: regEmail.trim().toLowerCase(),
      password: regPassword,
      confirm_password: regConfirmPassword,
    };

    try {
      const res = await apiClient.auth.registerEmployee(payload);
      if (res?.success && res?.data) {
        setRegistrationSuccess(res.data);
        setRegEmployeeId("");
        setRegEmail("");
        setRegPassword("");
        setRegConfirmPassword("");
        setRegValidationErrors({});
      } else {
        setRegFormError("Registration could not be completed. Please check your credentials.");
      }
    } catch (err) {
      const errorMsg =
        err.data?.error?.message ||
        err.message ||
        "Employee registration failed. Please verify your administrator-issued Employee ID.";
      setRegFormError(errorMsg);
    } finally {
      setIsRegSubmitting(false);
    }
  };

  // Sign-Out Handler
  const handleSignOut = async () => {
    try {
      if (supabase) {
        await supabase.auth.signOut();
      }
    } catch (err) {
      console.error("[RetainIQ Auth] Sign out error:", err);
    } finally {
      setVerifiedIdentity(null);
      setVerificationStatus("idle");
      setVerificationError(null);
      setEmail("");
      setPassword("");
    }
  };

  // Retry Verification Handler
  const handleRetryVerification = () => {
    if (session?.access_token) {
      setVerificationStatus("verifying");
      setVerificationError(null);
      apiClient.auth
        .getProfile()
        .then((res) => {
          if (res?.success && res?.data) {
            setVerifiedIdentity(res.data);
            setVerificationStatus("verified");
          }
        })
        .catch((err) => {
          setVerificationError(err.message || "Verification failed");
          setVerificationStatus("failed");
        });
    }
  };

  // Navigation Helper
  const handleBackToHome = () => {
    if (onNavigate) {
      onNavigate("/");
    } else {
      window.location.pathname = "/";
    }
  };

  return (
    <div className="min-h-screen bg-bg text-text-primary flex flex-col justify-between selection:bg-electric selection:text-white">
      {/* Top Navigation Bar */}
      <header className="border-b border-border bg-surface/90 backdrop-blur-sm py-3">
        <Container size="default" className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <button
              onClick={handleBackToHome}
              className="flex items-center gap-2.5 group focus-visible:ring-2 focus-visible:ring-electric rounded-lg p-1 text-left"
              aria-label="Return to RetainIQ Home"
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
              <div className="flex flex-col">
                <span className="font-heading font-semibold text-lg text-midnight tracking-tight">
                  Retain<span className="text-electric">IQ</span>
                </span>
                <span className="text-[10px] font-mono text-text-secondary tracking-widest uppercase">
                  Internal Enterprise Portal
                </span>
              </div>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle size="sm" />
            <Button
              variant="ghost"
              size="sm"
              icon={ArrowLeft}
              onClick={handleBackToHome}
              className="text-text-secondary hover:text-midnight font-medium text-xs sm:text-sm"
            >
              Public Showcase
            </Button>
          </div>
        </Container>
      </header>

      {/* Main Container */}
      <main className="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          {/* Card Container */}
          <div className="bg-surface border border-border rounded-xl shadow-card p-6 sm:p-8">
            {/* ========================================================== */}
            {/* STATE A: SAFE AUTHENTICATED / PENDING-ACCESS VIEW           */}
            {/* ========================================================== */}
            {session && user ? (
              <div className="space-y-6">
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mb-3">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <span className="px-2.5 py-0.5 text-[10px] font-mono font-medium uppercase rounded bg-emerald-50 text-emerald-700 border border-emerald-200 inline-block mb-2">
                    AUTHENTICATION SUCCESSFUL
                  </span>
                  <h2 className="font-heading text-xl font-semibold text-midnight tracking-tight">
                    Identity Verified
                  </h2>
                  <p className="text-xs text-text-secondary mt-1">
                    Supabase ES256 session established for enterprise account.
                  </p>
                </div>

                {/* Account Details Pill */}
                <div className="p-3.5 rounded-lg bg-bg border border-border text-xs space-y-2">
                  <div className="flex justify-between items-center text-text-muted">
                    <span>Signed-In Email:</span>
                    <span className="font-mono font-semibold text-midnight text-[11px] truncate max-w-[200px]">
                      {user.email || "No email claim"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-text-muted">
                    <span>Subject Identifier:</span>
                    <span className="font-mono text-text-secondary text-[10px] truncate max-w-[190px]">
                      {user.id}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-text-muted">
                    <span>Backend Status:</span>
                    <span className="font-medium text-electric flex items-center gap-1">
                      {verificationStatus === "verifying" && (
                        <>
                          <Loader2 className="w-3 h-3 animate-spin" /> Verifying JWT...
                        </>
                      )}
                      {verificationStatus === "verified" && (
                        <>
                          <ShieldCheck className="w-3 h-3 text-success" /> ES256 Verified
                        </>
                      )}
                      {verificationStatus === "failed" && (
                        <>
                          <AlertCircle className="w-3 h-3 text-error" /> Check Failed
                        </>
                      )}
                    </span>
                  </div>
                </div>

                {/* Dynamic Status Presentation Box */}
                {isAdmin ? (
                  <div className="p-4 rounded-lg bg-midnight border border-slate-800 text-white text-xs space-y-2.5">
                    <div className="flex items-center gap-2 font-heading font-semibold text-xs text-white">
                      <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>Administrator Privileges Verified</span>
                    </div>
                    <p className="text-slate-400 leading-relaxed text-[11.5px]">
                      Your account holds active, verified administrator privileges for RetainIQ.
                    </p>
                    <div className="pt-1">
                      <Button
                        variant="primary"
                        size="md"
                        onClick={() => (onNavigate ? onNavigate("/admin") : (window.location.pathname = "/admin"))}
                        icon={ArrowRight}
                        className="w-full justify-center text-xs font-semibold"
                      >
                        Launch Administrator Portal (/admin)
                      </Button>
                    </div>
                  </div>
                ) : employeeStatusCategory === "APPROVED" && employeeProfile ? (
                  <div className="p-4 rounded-lg bg-emerald-50/80 border border-emerald-200 text-emerald-950 text-xs space-y-2.5">
                    <div className="flex items-center gap-2 font-heading font-semibold text-xs text-emerald-950">
                      <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>Employee Clearance Approved</span>
                    </div>
                    <p className="text-emerald-800 leading-relaxed text-[11.5px]">
                      Your account holds active, verified employee clearance for the RetainIQ portal.
                    </p>
                    <div className="pt-1">
                      <Button
                        variant="primary"
                        size="md"
                        onClick={() => (onNavigate ? onNavigate("/employee/dashboard") : (window.location.pathname = "/employee/dashboard"))}
                        icon={ArrowRight}
                        className="w-full justify-center text-xs font-semibold"
                      >
                        Launch Employee Dashboard ({employeeProfile.employee_id})
                      </Button>
                    </div>
                  </div>
                ) : employeeStatusCategory === "REJECTED" ? (
                  <div className="p-4 rounded-lg bg-rose-50/80 border border-rose-200 text-rose-950 text-xs space-y-2">
                    <div className="flex items-center gap-2 font-heading font-semibold text-xs text-rose-950">
                      <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                      <span>Registration Not Approved</span>
                    </div>
                    <p className="text-rose-800 leading-relaxed text-[11.5px]">
                      Your employee registration was reviewed and rejected by an administrator. Please contact your department supervisor.
                    </p>
                  </div>
                ) : employeeStatusCategory === "SUSPENDED" ? (
                  <div className="p-4 rounded-lg bg-slate-100 border border-slate-200 text-slate-800 text-xs space-y-2">
                    <div className="flex items-center gap-2 font-heading font-semibold text-xs text-slate-950">
                      <ShieldAlert className="w-4 h-4 text-slate-700 shrink-0" />
                      <span>Employee Account Suspended</span>
                    </div>
                    <p className="text-slate-600 leading-relaxed text-[11.5px]">
                      This employee account has been temporarily suspended by an administrator.
                    </p>
                  </div>
                ) : verificationStatus === "failed" ? (
                  <div className="p-4 rounded-lg bg-rose-50/80 border border-rose-200 text-rose-950 text-xs space-y-2">
                    <div className="flex items-center gap-2 font-heading font-semibold text-xs text-rose-950">
                      <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                      <span>Backend Authorization Service Unreachable</span>
                    </div>
                    <p className="text-rose-800 leading-relaxed text-[11.5px]">
                      {verificationError || "The frontend client was unable to contact the RetainIQ backend API service."}
                    </p>
                    <p className="text-rose-700 font-mono text-[10.5px]">
                      Target API: {(import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000")}
                    </p>
                  </div>
                ) : (
                  <div className="p-4 rounded-lg bg-amber-50/80 border border-amber-200 text-amber-950 text-xs space-y-2">
                    <div className="flex items-center gap-2 font-heading font-semibold text-xs text-amber-950">
                      <Building2 className="w-4 h-4 text-amber-700 shrink-0" />
                      <span>Employee Access Authorization Pending</span>
                    </div>
                    <p className="text-amber-800 leading-relaxed text-[11.5px]">
                      Your account identity has been verified via the backend JWT/JWKS engine. However,
                      employee portal authorization is restricted to approved accounts.
                    </p>
                    <p className="text-amber-700 font-mono text-[10.5px]">
                      Policy: ADMIN-CONTROLLED EMPLOYEE ACCOUNTS
                    </p>
                  </div>
                )}

                {/* Security Restriction Notice (only if not approved and not admin) */}
                {!isAdmin && employeeStatusCategory !== "APPROVED" && (
                  <div className="p-3 rounded-lg bg-bg border border-border text-[11px] text-text-muted flex items-start gap-2">
                    <ShieldAlert className="w-4 h-4 text-text-muted shrink-0 mt-0.5" />
                    <span>
                      Customer analytics, churn risk scores, and retention actions remain locked until
                      your role is provisioned by a system administrator.
                    </span>
                  </div>
                )}

                {/* Verification Error Box */}
                {!isAdmin && verificationError && employeeStatusCategory !== "APPROVED" && (
                  <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start justify-between gap-2">
                    <span>{verificationError}</span>
                    <button
                      onClick={handleRetryVerification}
                      className="underline font-semibold shrink-0 hover:text-rose-900"
                    >
                      Retry
                    </button>
                  </div>
                )}

                {/* Actions */}
                <div className="space-y-3 pt-2">
                  <Button
                    variant="outline"
                    size="md"
                    onClick={handleSignOut}
                    icon={LogOut}
                    className="w-full justify-center text-xs font-semibold"
                  >
                    Sign Out of RetainIQ
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleBackToHome}
                    icon={ArrowLeft}
                    className="w-full justify-center text-xs text-text-secondary"
                  >
                    Return to Public Showcase
                  </Button>
                </div>
              </div>
            ) : (
              /* ========================================================== */
              /* STATE B: TWO-TAB AUTHENTICATION & REGISTRATION INTERFACE   */
              /* ========================================================== */
              <div>
                {/* Tab Switcher Header */}
                <div className="flex items-center p-1 bg-bg border border-border rounded-lg mb-6">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab("login");
                      setFormError(null);
                    }}
                    className={`flex-1 py-1.5 text-xs font-heading font-medium rounded-md transition-colors ${activeTab === "login"
                        ? "bg-surface text-midnight shadow-subtle border border-border"
                        : "text-text-secondary hover:text-midnight"
                      }`}
                  >
                    Sign In
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab("register");
                      setRegFormError(null);
                    }}
                    className={`flex-1 py-1.5 text-xs font-heading font-medium rounded-md transition-colors ${activeTab === "register"
                        ? "bg-surface text-midnight shadow-subtle border border-border"
                        : "text-text-secondary hover:text-midnight"
                      }`}
                  >
                    Register as an Employee
                  </button>
                </div>

                {activeTab === "login" ? (
                  /* ------------------------------------------------------ */
                  /* TAB 1: EMPLOYEE SIGN IN FORM                           */
                  /* ------------------------------------------------------ */
                  <div>
                    <div className="text-center mb-6">
                      <div className="w-10 h-10 mx-auto rounded-lg bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center mb-3">
                        <Lock className="w-5 h-5" />
                      </div>
                      <span className="px-2 py-0.5 text-[10px] font-mono font-medium uppercase rounded bg-slate-100 text-slate-700 border border-slate-200 inline-block mb-1.5">
                        INTERNAL PORTAL
                      </span>
                      <h1 className="font-heading text-xl font-semibold text-midnight tracking-tight">
                        Employee Sign In
                      </h1>
                      <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                        Access the RetainIQ retention intelligence and customer diagnostic portal.
                      </p>
                    </div>

                    {formError && (
                      <div
                        role="alert"
                        className="mb-5 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5"
                      >
                        <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{formError}</span>
                      </div>
                    )}

                    <form onSubmit={handleLoginSubmit} noValidate className="space-y-4.5 sm:space-y-5">
                      {/* Work Email */}
                      <div>
                        <label
                          htmlFor="employee-email"
                          className="block text-xs font-heading font-semibold text-midnight mb-1.5"
                        >
                          Enterprise Work Email
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                            <Mail className="w-4 h-4" />
                          </div>
                          <input
                            id="employee-email"
                            type="email"
                            value={email}
                            onChange={(e) => {
                              setEmail(e.target.value);
                              if (validationErrors.email) {
                                setValidationErrors((prev) => ({ ...prev, email: null }));
                              }
                            }}
                            autoComplete="email"
                            placeholder="analyst@retainiq.internal"
                            disabled={isSubmitting}
                            aria-invalid={Boolean(validationErrors.email)}
                            aria-describedby={validationErrors.email ? "email-error" : undefined}
                            className={`w-full pl-10 pr-3.5 py-2.5 text-sm rounded-lg border bg-surface transition-colors focus:outline-none focus:ring-2 focus:ring-electric ${validationErrors.email
                                ? "border-rose-300 bg-rose-50/20 text-rose-900"
                                : "border-border text-text-primary hover:border-slate-400"
                              }`}
                          />
                        </div>
                        {validationErrors.email && (
                          <p id="email-error" className="mt-1 text-xs text-rose-600 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3 shrink-0" />
                            {validationErrors.email}
                          </p>
                        )}
                      </div>

                      {/* Password */}
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <label
                            htmlFor="employee-password"
                            className="block text-xs font-heading font-semibold text-midnight"
                          >
                            Account Password
                          </label>
                        </div>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                            <Lock className="w-4 h-4" />
                          </div>
                          <input
                            id="employee-password"
                            type={showPassword ? "text" : "password"}
                            value={password}
                            onChange={(e) => {
                              setPassword(e.target.value);
                              if (validationErrors.password) {
                                setValidationErrors((prev) => ({ ...prev, password: null }));
                              }
                            }}
                            autoComplete="current-password"
                            placeholder="••••••••••••"
                            disabled={isSubmitting}
                            aria-invalid={Boolean(validationErrors.password)}
                            aria-describedby={validationErrors.password ? "password-error" : undefined}
                            className={`w-full pl-10 pr-10 py-2.5 text-sm rounded-lg border bg-surface transition-colors focus:outline-none focus:ring-2 focus:ring-electric ${validationErrors.password
                                ? "border-rose-300 bg-rose-50/20 text-rose-900"
                                : "border-border text-text-primary hover:border-slate-400"
                              }`}
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-text-primary focus:outline-none focus-visible:text-electric"
                            aria-label={showPassword ? "Hide password" : "Show password"}
                          >
                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                        {validationErrors.password && (
                          <p id="password-error" className="mt-1 text-xs text-rose-600 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3 shrink-0" />
                            {validationErrors.password}
                          </p>
                        )}
                      </div>

                      {/* Submit Button */}
                      <div className="pt-2">
                        <Button
                          type="submit"
                          variant="primary"
                          size="md"
                          disabled={isSubmitting}
                          className="w-full justify-center font-semibold text-sm"
                        >
                          {isSubmitting ? (
                            <span className="flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin" /> Signing In...
                            </span>
                          ) : (
                            <span className="flex items-center gap-2">
                              Sign In to Portal <ArrowRight className="w-4 h-4" />
                            </span>
                          )}
                        </Button>
                      </div>
                    </form>
                  </div>
                ) : (
                  /* ------------------------------------------------------ */
                  /* TAB 2: EMPLOYEE REGISTRATION FORM & SUCCESS STATE       */
                  /* ------------------------------------------------------ */
                  <div>
                    {registrationSuccess ? (
                      /* Registration Submitted Successfully View */
                      <div className="space-y-6">
                        <div className="text-center">
                          <div className="w-12 h-12 mx-auto rounded-lg bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center mb-3">
                            <Clock className="w-6 h-6" />
                          </div>
                          <span className="px-2 py-0.5 text-[10px] font-mono font-medium uppercase rounded bg-amber-100 text-amber-800 border border-amber-200 inline-block mb-1.5">
                            AWAITING APPROVAL
                          </span>
                          <h2 className="font-heading text-xl font-semibold text-midnight tracking-tight">
                            Registration Submitted Successfully
                          </h2>
                          <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                            Your Employee ID and work email have been submitted. Your account is awaiting administrator approval. You will be able to access the RetainIQ employee portal after approval.
                          </p>
                        </div>

                        {/* Submission Details Box */}
                        <div className="p-3.5 rounded-lg bg-bg border border-border text-xs space-y-2.5">
                          <div className="flex justify-between items-center text-text-muted">
                            <span>Employee ID:</span>
                            <span className="font-mono font-bold text-midnight text-[11.5px]">
                              {registrationSuccess.employee_id}
                            </span>
                          </div>
                          <div className="flex justify-between items-center text-text-muted">
                            <span>Submitted Work Email:</span>
                            <span className="font-mono font-semibold text-midnight text-[11px] truncate max-w-[200px]">
                              {registrationSuccess.work_email}
                            </span>
                          </div>
                          <div className="flex justify-between items-center text-text-muted">
                            <span>Account Status:</span>
                            <span className="font-mono font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-[10.5px]">
                              PENDING APPROVAL
                            </span>
                          </div>
                        </div>

                        {/* Safety Notice: No Customer Data Access */}
                        <div className="p-3.5 rounded-lg bg-amber-50/80 border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
                          <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                          <span className="leading-relaxed text-[11.5px]">
                            Protected customer intelligence, churn predictions, and risk exploration
                            tools remain locked until an administrator reviews and approves this registration.
                          </span>
                        </div>

                        {/* Switch to Login Action */}
                        <div className="pt-2">
                          <Button
                            variant="primary"
                            size="md"
                            onClick={() => {
                              setRegistrationSuccess(null);
                              setActiveTab("login");
                            }}
                            className="w-full justify-center text-xs font-semibold"
                          >
                            Return to Sign In
                          </Button>
                        </div>
                      </div>
                    ) : (
                      /* Registration Input Form */
                      <div>
                        <div className="text-center mb-6">
                          <div className="w-10 h-10 mx-auto rounded-lg bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center mb-3">
                            <UserPlus className="w-5 h-5 text-midnight" />
                          </div>
                          <span className="px-2 py-0.5 text-[10px] font-mono font-medium uppercase rounded bg-slate-100 text-slate-700 border border-slate-200 inline-block mb-1.5">
                            EMPLOYEE ONBOARDING
                          </span>
                          <h2 className="font-heading text-xl font-semibold text-midnight tracking-tight">
                            Register as an Employee
                          </h2>
                          <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                            Enter your pre-issued Employee ID and work email to request portal access.
                          </p>
                        </div>

                        {regFormError && (
                          <div
                            role="alert"
                            className="mb-5 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5"
                          >
                            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                            <span className="leading-relaxed">{regFormError}</span>
                          </div>
                        )}

                        <form onSubmit={handleRegisterSubmit} noValidate className="space-y-4.5 sm:space-y-5">
                          {/* Pre-Issued Employee ID */}
                          <div>
                            <label
                              htmlFor="reg-employee-id"
                              className="block text-xs font-heading font-semibold text-midnight mb-1.5"
                            >
                              Administrator-Issued Employee ID
                            </label>
                            <div className="relative">
                              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                                <IdCard className="w-4 h-4" />
                              </div>
                              <input
                                id="reg-employee-id"
                                type="text"
                                value={regEmployeeId}
                                onChange={(e) => {
                                  setRegEmployeeId(e.target.value);
                                  if (regValidationErrors.employeeId) {
                                    setRegValidationErrors((prev) => ({ ...prev, employeeId: null }));
                                  }
                                }}
                                placeholder="EMP-2026-002"
                                disabled={isRegSubmitting}
                                aria-invalid={Boolean(regValidationErrors.employeeId)}
                                aria-describedby={regValidationErrors.employeeId ? "reg-employee-id-error" : undefined}
                                className={`w-full pl-10 pr-3.5 py-2.5 text-sm rounded-lg border bg-surface uppercase font-mono transition-colors focus:outline-none focus:ring-2 focus:ring-electric ${regValidationErrors.employeeId
                                    ? "border-rose-300 bg-rose-50/20 text-rose-900"
                                    : "border-border text-text-primary hover:border-slate-400"
                                  }`}
                              />
                            </div>
                            {regValidationErrors.employeeId && (
                              <p id="reg-employee-id-error" className="mt-1 text-xs text-rose-600 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 shrink-0" />
                                {regValidationErrors.employeeId}
                              </p>
                            )}
                          </div>

                          {/* Work Email */}
                          <div>
                            <label
                              htmlFor="reg-email"
                              className="block text-xs font-heading font-semibold text-midnight mb-1.5"
                            >
                              Enterprise Work Email
                            </label>
                            <div className="relative">
                              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                                <Mail className="w-4 h-4" />
                              </div>
                              <input
                                id="reg-email"
                                type="email"
                                value={regEmail}
                                onChange={(e) => {
                                  setRegEmail(e.target.value);
                                  if (regValidationErrors.email) {
                                    setRegValidationErrors((prev) => ({ ...prev, email: null }));
                                  }
                                }}
                                autoComplete="email"
                                placeholder="new_hire@retainiq.internal"
                                disabled={isRegSubmitting}
                                aria-invalid={Boolean(regValidationErrors.email)}
                                aria-describedby={regValidationErrors.email ? "reg-email-error" : undefined}
                                className={`w-full pl-10 pr-3.5 py-2.5 text-sm rounded-lg border bg-surface transition-colors focus:outline-none focus:ring-2 focus:ring-electric ${regValidationErrors.email
                                    ? "border-rose-300 bg-rose-50/20 text-rose-900"
                                    : "border-border text-text-primary hover:border-slate-400"
                                  }`}
                              />
                            </div>
                            {regValidationErrors.email && (
                              <p id="reg-email-error" className="mt-1 text-xs text-rose-600 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 shrink-0" />
                                {regValidationErrors.email}
                              </p>
                            )}
                          </div>

                          {/* Password */}
                          <div>
                            <label
                              htmlFor="reg-password"
                              className="block text-xs font-heading font-semibold text-midnight mb-1.5"
                            >
                              Create Password (min. 8 characters)
                            </label>
                            <div className="relative">
                              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                                <Lock className="w-4 h-4" />
                              </div>
                              <input
                                id="reg-password"
                                type={showRegPassword ? "text" : "password"}
                                value={regPassword}
                                onChange={(e) => {
                                  setRegPassword(e.target.value);
                                  if (regValidationErrors.password) {
                                    setRegValidationErrors((prev) => ({ ...prev, password: null }));
                                  }
                                }}
                                autoComplete="new-password"
                                placeholder="••••••••••••"
                                disabled={isRegSubmitting}
                                aria-invalid={Boolean(regValidationErrors.password)}
                                aria-describedby={regValidationErrors.password ? "reg-password-error" : undefined}
                                className={`w-full pl-10 pr-10 py-2.5 text-sm rounded-lg border bg-surface transition-colors focus:outline-none focus:ring-2 focus:ring-electric ${regValidationErrors.password
                                    ? "border-rose-300 bg-rose-50/20 text-rose-900"
                                    : "border-border text-text-primary hover:border-slate-400"
                                  }`}
                              />
                              <button
                                type="button"
                                onClick={() => setShowRegPassword(!showRegPassword)}
                                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-text-muted hover:text-text-primary focus:outline-none focus-visible:text-electric"
                                aria-label={showRegPassword ? "Hide password" : "Show password"}
                              >
                                {showRegPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </button>
                            </div>
                            {regValidationErrors.password && (
                              <p id="reg-password-error" className="mt-1 text-xs text-rose-600 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 shrink-0" />
                                {regValidationErrors.password}
                              </p>
                            )}
                          </div>

                          {/* Confirm Password */}
                          <div>
                            <label
                              htmlFor="reg-confirm-password"
                              className="block text-xs font-heading font-semibold text-midnight mb-1.5"
                            >
                              Confirm Password
                            </label>
                            <div className="relative">
                              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                                <Lock className="w-4 h-4" />
                              </div>
                              <input
                                id="reg-confirm-password"
                                type={showRegConfirmPassword ? "text" : "password"}
                                value={regConfirmPassword}
                                onChange={(e) => {
                                  setRegConfirmPassword(e.target.value);
                                  if (regValidationErrors.confirmPassword) {
                                    setRegValidationErrors((prev) => ({ ...prev, confirmPassword: null }));
                                  }
                                }}
                                autoComplete="new-password"
                                placeholder="••••••••••••"
                                disabled={isRegSubmitting}
                                aria-invalid={Boolean(regValidationErrors.confirmPassword)}
                                aria-describedby={regValidationErrors.confirmPassword ? "reg-confirm-password-error" : undefined}
                                className={`w-full pl-10 pr-10 py-2.5 text-sm rounded-lg border bg-surface transition-colors focus:outline-none focus:ring-2 focus:ring-electric ${regValidationErrors.confirmPassword
                                    ? "border-rose-300 bg-rose-50/20 text-rose-900"
                                    : "border-border text-text-primary hover:border-slate-400"
                                  }`}
                              />
                              <button
                                type="button"
                                onClick={() => setShowRegConfirmPassword(!showRegConfirmPassword)}
                                className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-text-primary focus:outline-none focus-visible:text-electric"
                                aria-label={showRegConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                              >
                                {showRegConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </button>
                            </div>
                            {regValidationErrors.confirmPassword && (
                              <p id="reg-confirm-password-error" className="mt-1 text-xs text-rose-600 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 shrink-0" />
                                {regValidationErrors.confirmPassword}
                              </p>
                            )}
                          </div>

                          {/* Submit Button */}
                          <div className="pt-2">
                            <Button
                              type="submit"
                              variant="primary"
                              size="md"
                              disabled={isRegSubmitting}
                              className="w-full justify-center font-semibold text-sm"
                            >
                              {isRegSubmitting ? (
                                <span className="flex items-center gap-2">
                                  <Loader2 className="w-4 h-4 animate-spin" /> Submitting Registration...
                                </span>
                              ) : (
                                <span className="flex items-center gap-2">
                                  Submit Registration <ArrowRight className="w-4 h-4" />
                                </span>
                              )}
                            </Button>
                          </div>
                        </form>
                      </div>
                    )}
                  </div>
                )}

                {/* Admin-Controlled Policy Notice */}
                <div className="mt-6 pt-5 border-t border-border/80 text-center">
                  <div className="flex items-center justify-center gap-1.5 text-xs text-text-secondary font-medium mb-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-electric" />
                    <span>Admin-Controlled Access Policy</span>
                  </div>
                  <p className="text-[11px] text-text-muted leading-relaxed">
                    Employee portal accounts are provisioned exclusively by system administrators.
                    Registrations require pre-issued Employee IDs and administrator approval.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Footer Security Badges */}
          <div className="mt-6 text-center text-xs text-text-muted flex items-center justify-center gap-3">
            <span>ES256 JWKS Cryptography</span>
            <span>•</span>
            <span>FastAPI REST Backend</span>
            <span>•</span>
            <span>Supabase Auth</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/80 bg-surface py-4 text-center text-xs text-text-secondary">
        <p>© 2026 RetainIQ Intelligence System • BCA AI & ML Final Year Capstone Project</p>
      </footer>
    </div>
  );
}
