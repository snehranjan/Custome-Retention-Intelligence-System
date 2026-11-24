import React from "react";
import { Mail, ExternalLink, ShieldCheck, Cpu, Database, Activity, Lock, Layers } from "lucide-react";
import { Container } from "../ui/Container";

/**
 * RetainIQ Comprehensive Website Footer (Phase 8.4 Pre-Deployment Polish)
 * 
 * Requirements:
 * - Brand identity with SVG logo mark and academic context.
 * - Working internal navigation links.
 * - Genuine API documentation links (Swagger, Health).
 * - Clickable mailto support link.
 * - Dynamic calendar copyright year.
 * - Responsive 1 to 4 column mobile-friendly layout.
 */
export function Footer({ onNavigate }) {
  const currentYear = new Date().getFullYear();

  const handleLinkClick = (e, target) => {
    e.preventDefault();
    if (target.startsWith("#")) {
      if (window.location.pathname !== "/") {
        if (onNavigate) {
          onNavigate("/" + target);
        } else {
          window.location.href = "/" + target;
        }
        return;
      }
      const targetId = target.replace("#", "");
      if (targetId === "hero") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        const elem = document.getElementById(targetId);
        if (elem) {
          elem.scrollIntoView({ behavior: "smooth" });
        }
      }
    } else {
      if (onNavigate) {
        onNavigate(target);
      } else {
        window.location.pathname = target;
      }
    }
  };

  return (
    <footer className="border-t border-border bg-surface text-text-primary pt-12 pb-8">
      <Container size="default" className="space-y-10">
        {/* Main 4-Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-10">
          {/* Column 1: Brand & Academic Project Overview */}
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-midnight flex items-center justify-center border border-slate-800">
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
                <span className="text-[10px] font-mono text-text-secondary tracking-wider uppercase">
                  Retention Intelligence
                </span>
              </div>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed">
              Enterprise customer retention intelligence system predicting churn risk, segmenting behavioral personas, and automating intervention strategies for Indian e-commerce.
            </p>

            <div className="pt-1">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-mono font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                System Active • Production Checkpoint
              </span>
            </div>
          </div>

          {/* Column 2: Platform Navigation */}
          <div className="space-y-3">
            <h4 className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
              Platform Architecture
            </h4>
            <ul className="space-y-2 text-xs text-text-secondary">
              <li>
                <a
                  href="#hero"
                  onClick={(e) => handleLinkClick(e, "#hero")}
                  className="hover:text-electric transition-colors focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5 inline-block"
                >
                  System Overview
                </a>
              </li>
              <li>
                <a
                  href="#platform"
                  onClick={(e) => handleLinkClick(e, "#platform")}
                  className="hover:text-electric transition-colors focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5 inline-block"
                >
                  Platform Highlights
                </a>
              </li>
              <li>
                <a
                  href="#features"
                  onClick={(e) => handleLinkClick(e, "#features")}
                  className="hover:text-electric transition-colors focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5 inline-block"
                >
                  Feature Deep-Dive
                </a>
              </li>
              <li>
                <a
                  href="#how-it-works"
                  onClick={(e) => handleLinkClick(e, "#how-it-works")}
                  className="hover:text-electric transition-colors focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5 inline-block"
                >
                  ML Architecture & Pipeline
                </a>
              </li>
              <li>
                <a
                  href="#about"
                  onClick={(e) => handleLinkClick(e, "#about")}
                  className="hover:text-electric transition-colors focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5 inline-block"
                >
                  Academic Scope & Methodology
                </a>
              </li>
            </ul>
          </div>

          {/* Column 3: Authenticated Portals */}
          <div className="space-y-3">
            <h4 className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
              Access Portals
            </h4>
            <ul className="space-y-2 text-xs text-text-secondary">
              <li>
                <a
                  href="/employee/login"
                  onClick={(e) => handleLinkClick(e, "/employee/login")}
                  className="hover:text-electric transition-colors flex items-center gap-1.5 focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5"
                >
                  <Lock className="w-3.5 h-3.5 text-text-secondary" />
                  <span>Employee Sign In</span>
                </a>
              </li>
              <li>
                <a
                  href="/admin"
                  onClick={(e) => handleLinkClick(e, "/admin")}
                  className="hover:text-electric transition-colors flex items-center gap-1.5 focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-text-secondary" />
                  <span>Administrator Portal</span>
                </a>
              </li>
              <li>
                <a
                  href="/employee/dashboard"
                  onClick={(e) => handleLinkClick(e, "/employee/dashboard")}
                  className="hover:text-electric transition-colors flex items-center gap-1.5 focus-visible:ring-1 focus-visible:ring-electric rounded py-0.5"
                >
                  <Activity className="w-3.5 h-3.5 text-text-secondary" />
                  <span>Intelligence Dashboard</span>
                </a>
              </li>
            </ul>

            <div className="pt-2">
              <h5 className="font-heading font-semibold text-[11px] uppercase tracking-wider text-text-muted mb-1.5">
                Live Backend Services
              </h5>
              <div className="space-y-1.5 text-xs text-text-secondary">
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-electric transition-colors flex items-center gap-1.5 font-mono text-[11px]"
                >
                  <span>Interactive API Docs</span>
                  <ExternalLink className="w-3 h-3 text-text-muted" />
                </a>
                <a
                  href="http://127.0.0.1:8000/api/v1/health"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-electric transition-colors flex items-center gap-1.5 font-mono text-[11px]"
                >
                  <span>System Health Endpoint</span>
                  <ExternalLink className="w-3 h-3 text-text-muted" />
                </a>
              </div>
            </div>
          </div>

          {/* Column 4: Academic Capstone & Contact */}
          <div className="space-y-3">
            <h4 className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
              Academic Project & Support
            </h4>
            <div className="text-xs text-text-secondary space-y-2">
              <p className="leading-relaxed">
                Bachelor of Computer Applications (AI & ML) Final Year Capstone Project.
              </p>
              <div className="p-3 bg-bg border border-border rounded-lg space-y-1.5">
                <span className="font-mono text-[10px] uppercase text-text-muted font-semibold block">
                  Project Inquiries & Support
                </span>
                <a
                  href="mailto:support@retainiq.internal"
                  className="text-electric hover:underline flex items-center gap-1.5 font-mono text-[11px]"
                  title="Contact Project Support"
                >
                  <Mail className="w-3.5 h-3.5" />
                  <span>support@retainiq.internal</span>
                </a>
              </div>
              <p className="text-[11px] text-text-muted leading-relaxed">
                Demonstration platform evaluated under synthetic conditions with a strict Dec 31, 2025 observation cutoff.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bar: Copyright & Tech Stack */}
        <div className="pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-text-secondary">
          <p>© {currentYear} RetainIQ. All rights reserved.</p>

          <div className="flex flex-wrap items-center gap-3 font-mono text-[11px] text-text-muted">
            <span>React 19</span>
            <span>•</span>
            <span>Vite 6</span>
            <span>•</span>
            <span>FastAPI REST</span>
            <span>•</span>
            <span>scikit-learn</span>
            <span>•</span>
            <span>Supabase Auth (ES256)</span>
          </div>
        </div>
      </Container>
    </footer>
  );
}
