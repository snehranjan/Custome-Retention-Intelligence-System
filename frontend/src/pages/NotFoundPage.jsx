import React, { useEffect } from "react";
import { ArrowLeft, Home, Lock, Shield, Compass, Search } from "lucide-react";
import { Container } from "../components/ui/Container";
import { Button } from "../components/ui/Button";
import { ThemeToggle } from "../components/ui/ThemeToggle";

/**
 * RetainIQ Branded 404 Page (Phase 8.4 Pre-Deployment Polish)
 * 
 * Requirements:
 * - Clear 404 status badge and heading.
 * - Friendly explanation that the requested URL cannot be found.
 * - Navigation buttons returning to Homepage, Employee Login, or Admin Portal.
 * - Consistent RetainIQ visual branding (Midnight Navy, Electric Blue, Cyan, Slate 50).
 * - Fully responsive across 1440px, 1024px, 768px, 430px, 390px, 360px.
 */
export function NotFoundPage({ onNavigate }) {
  useEffect(() => {
    document.title = "Page Not Found | RetainIQ";
  }, []);

  const handleHomeClick = () => {
    if (onNavigate) {
      onNavigate("/");
    } else {
      window.location.pathname = "/";
    }
  };

  const handleLoginClick = () => {
    if (onNavigate) {
      onNavigate("/employee/login");
    } else {
      window.location.pathname = "/employee/login";
    }
  };

  const handleAdminClick = () => {
    if (onNavigate) {
      onNavigate("/admin");
    } else {
      window.location.pathname = "/admin";
    }
  };

  return (
    <div className="min-h-screen bg-bg text-text-primary flex flex-col justify-between selection:bg-electric selection:text-white">
      {/* Top Minimal Header */}
      <header className="border-b border-border bg-surface/90 backdrop-blur-sm py-3">
        <Container size="default" className="flex items-center justify-between">
          <button
            onClick={handleHomeClick}
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
                Customer Retention Intelligence
              </span>
            </div>
          </button>

          <div className="flex items-center gap-2">
            <ThemeToggle size="sm" />
            <Button
              variant="ghost"
              size="sm"
              icon={ArrowLeft}
              onClick={handleHomeClick}
              className="text-text-secondary hover:text-midnight font-medium text-xs sm:text-sm"
            >
              Return to Home
            </Button>
          </div>
        </Container>
      </header>

      {/* Main 404 Card Content */}
      <main className="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-lg text-center">
          <div className="bg-surface border border-border rounded-xl shadow-card p-6 sm:p-8 space-y-6">
            {/* 404 Badge & Visual Mark */}
            <div className="w-16 h-16 mx-auto rounded-xl bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center">
              <Compass className="w-8 h-8 text-slate-700" />
            </div>

            <div className="space-y-2">
              <span className="px-2.5 py-0.5 text-xs font-mono font-medium uppercase rounded bg-slate-100 text-slate-700 border border-slate-200 inline-block">
                HTTP 404 • ROUTE NOT FOUND
              </span>
              <h1 className="font-heading font-semibold text-2xl sm:text-3xl text-midnight tracking-tight">
                Page Not Found
              </h1>
              <p className="text-sm text-text-secondary leading-relaxed max-w-sm mx-auto">
                The resource or portal route you requested does not exist or may have been relocated.
              </p>
            </div>

            {/* Quick Navigation Destination Options */}
            <div className="p-3.5 rounded-lg bg-bg border border-border text-left space-y-2 text-xs">
              <span className="text-[10px] font-mono font-medium uppercase text-text-muted block">
                AVAILABLE APPLICATION PORTALS
              </span>
              <div className="grid grid-cols-1 gap-2 pt-1">
                <button
                  onClick={handleHomeClick}
                  className="p-2.5 rounded-md bg-surface border border-border hover:border-slate-300 text-midnight font-medium flex items-center justify-between transition-colors text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <Home className="w-4 h-4 text-text-secondary" />
                    <span>Public Platform Showcase</span>
                  </div>
                  <span className="font-mono text-[10px] text-text-muted">/</span>
                </button>
                <button
                  onClick={handleLoginClick}
                  className="p-2.5 rounded-md bg-surface border border-border hover:border-slate-300 text-midnight font-medium flex items-center justify-between transition-colors text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <Lock className="w-4 h-4 text-text-secondary" />
                    <span>Employee Login & Dashboard</span>
                  </div>
                  <span className="font-mono text-[10px] text-text-muted">/employee/login</span>
                </button>
                <button
                  onClick={handleAdminClick}
                  className="p-2.5 rounded-md bg-surface border border-border hover:border-slate-300 text-midnight font-medium flex items-center justify-between transition-colors text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <Shield className="w-4 h-4 text-text-secondary" />
                    <span>Administrator Management Portal</span>
                  </div>
                  <span className="font-mono text-[10px] text-text-muted">/admin</span>
                </button>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Button
                variant="primary"
                size="md"
                icon={Home}
                onClick={handleHomeClick}
                className="w-full sm:w-auto justify-center text-xs font-semibold"
              >
                Back to Homepage
              </Button>
              <Button
                variant="outline"
                size="md"
                icon={Lock}
                onClick={handleLoginClick}
                className="w-full sm:w-auto justify-center text-xs font-semibold"
              >
                Employee Sign In
              </Button>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-surface py-4 text-center text-xs text-text-muted font-mono">
        © {new Date().getFullYear()} RetainIQ Intelligence System • Academic Demonstration
      </footer>
    </div>
  );
}
