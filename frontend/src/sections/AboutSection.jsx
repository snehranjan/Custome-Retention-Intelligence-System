import React from "react";
import {
  GraduationCap,
  BookOpen,
  Target,
  Layers,
  Cpu,
  Database,
  Server,
  Code2,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  BarChart3,
  Lightbulb,
  FileText,
  Lock,
  Compass,
  Zap,
  Clock,
  Terminal,
  Activity,
  Award,
} from "lucide-react";
import { Container } from "../components/ui/Container";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

/**
 * RetainIQ About & Academic Project Details Section (Phase 8.3.5)
 * Section Anchor: id="about"
 * 
 * Provides:
 * 1. Project Overview: Academic motivation, retention challenges in Indian e-commerce
 * 2. Problem Statement: Analytical challenges in customer defection detection
 * 3. 7 Verified Project Objectives: Data ingestion, preprocessing, KMeans, Random Forest, evaluation, rules, UI
 * 4. Academic Project Details Panel: Title, domain, capstone context, methodology
 * 5. Verified Technology Stack: React 19, FastAPI, scikit-learn, SQLite, Supabase ES256 JWKS
 * 6. Academic Scope & Scientific Disclosures: Synthetic data, uncalibrated scores, decision-support boundaries
 * 7. Phase 8.4 Employee Portal & Authentication Preview Banner
 */
export function AboutSection({ onNavigate, onOpenActionModal }) {
  // 7 Verified Project Objectives
  const projectObjectives = [
    {
      num: "01",
      title: "Historical Data Ingestion & Integrity",
      desc: "Synthesize and referentially validate 7,000 customer accounts and 84,225 transaction records with a strict Dec 31, 2025 observation cutoff.",
      icon: Database,
    },
    {
      num: "02",
      title: "Leakage-Free Preprocessing Pipeline",
      desc: "Engineer a ColumnTransformer with Log1p transformations, median imputation, missingness indicators, and within-fold correlation pruning.",
      icon: Cpu,
    },
    {
      num: "03",
      title: "Unsupervised Customer Segmentation",
      desc: "Group customers into 5 official behavioral personas using KMeans (K=5) on normalized RFM features with high multi-seed stability (ARI = 0.9931).",
      icon: Layers,
    },
    {
      num: "04",
      title: "Supervised Churn Risk Modeling",
      desc: "Train a production Random Forest classifier evaluating 43 raw Config D features at an immutable, pre-registered decision cutoff of τ = 0.50.",
      icon: Target,
    },
    {
      num: "05",
      title: "Independent Model Evaluation",
      desc: "Evaluate discrimination and calibration across a sealed holdout cohort of 1,500 unseen accounts without post-hoc threshold manipulation.",
      icon: Award,
    },
    {
      num: "06",
      title: "Explainable Retention Recommendations",
      desc: "Implement 8 deterministic business rules linking detected friction drivers to prioritized interventions with full managerial auditability.",
      icon: Lightbulb,
    },
    {
      num: "07",
      title: "Interactive Intelligence Interface",
      desc: "Deliver an accessible, responsive React 19 web application providing macro cohort analytics and customer-level diagnostic transparency.",
      icon: BarChart3,
    },
  ];

  // Verified Technology Stack
  const techStack = [
    {
      layer: "Frontend Interface",
      technologies: ["React 19", "Vite 6", "Tailwind CSS 3.4", "Framer Motion", "Lucide Icons"],
      desc: "Responsive web client delivering hero diagnostics, platform highlights, interactive workflow stepper, and architecture blueprints.",
      icon: Code2,
      badge: "Port 5173",
    },
    {
      layer: "Backend REST API",
      technologies: ["Python 3.12", "FastAPI 0.165", "Pydantic v2", "Uvicorn ASGI"],
      desc: "Asynchronous REST backend with strict schema validation, centralized error handling, and coordinator services.",
      icon: Server,
      badge: "Port 8000",
    },
    {
      layer: "Machine Learning Core",
      technologies: ["scikit-learn 1.9", "pandas 3.1", "NumPy 2.0", "joblib 1.6"],
      desc: "Pre-trained Random Forest pipeline (150 trees, depth 8) and KMeans cluster centroids (K=5) with cryptographic SHA-256 locks.",
      icon: Cpu,
      badge: "43 Features",
    },
    {
      layer: "Data Visualization & EDA",
      technologies: ["Matplotlib 3.11", "Seaborn 0.13"],
      desc: "Publication-grade exploratory analysis generating 15 verified statistical figures across historical distributions.",
      icon: BarChart3,
      badge: "15 Figures",
    },
    {
      layer: "Database & Security",
      technologies: ["SQLite (Local)", "Supabase Auth (ES256 JWKS)"],
      desc: "Local development persistence paired with asymmetric public-key JWT verification in FastAPI (Employee UI scheduled for Phase 8.4).",
      icon: Lock,
      badge: "ES256 JWKS",
    },
    {
      layer: "Testing & Governance",
      technologies: ["pytest 9.2", "Git / GitHub"],
      desc: "Master automated test suite certifying 160 out of 160 validation checks across 10 project milestones.",
      icon: ShieldCheck,
      badge: "160/160 Passed",
    },
  ];

  const handleEmployeePortalClick = () => {
    if (onNavigate) {
      onNavigate("/employee/login");
    } else if (onOpenActionModal) {
      onOpenActionModal({
        title: "Employee Portal & Authentication",
        subtitle: "Phase 8.4 Authentication UI",
        message:
          "The interactive Employee Login and Session Management portal is accessible. Sign in with your administrator-provisioned enterprise credentials.",
        icon: Lock,
        actionRoute: "/employee/login",
        actionLabel: "Open Employee Login",
      });
    }
  };

  return (
    <section
      id="about"
      className="relative py-16 sm:py-24 lg:py-28 bg-bg border-t border-border scroll-mt-20 overflow-hidden"
    >
      <Container size="default" className="relative z-10">
        {/* ======================================================== */}
        {/* SECTION HEADER                                            */}
        {/* ======================================================== */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-16 sm:mb-20">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-4">
            <GraduationCap className="w-3.5 h-3.5 text-text-secondary shrink-0" />
            <span>ACADEMIC CAPSTONE SPECIFICATION</span>
          </div>

          <h2 className="font-heading text-3xl sm:text-4xl font-semibold text-midnight tracking-tight leading-tight mb-3">
            About the Project
          </h2>

          <p className="text-base text-text-secondary leading-relaxed font-normal max-w-2xl">
            RetainIQ is an academic machine-learning project focused on understanding customer behaviour, predicting potential churn, and exploring data-driven customer retention strategies in the Indian e-commerce domain.
          </p>
        </div>

        {/* ======================================================== */}
        {/* SUBSECTION A & B: PROJECT OVERVIEW & PROBLEM STATEMENT   */}
        {/* ======================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-stretch mb-16 sm:mb-20">
          {/* Left Column: Academic Motivation & Overview */}
          <div className="lg:col-span-6 rounded-xl bg-surface border border-border shadow-card p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono font-medium uppercase tracking-wider text-text-secondary mb-3">
                <BookOpen className="w-4 h-4 text-text-secondary shrink-0" />
                <span>Academic Motivation & Context</span>
              </div>

              <h3 className="font-heading text-xl sm:text-2xl font-semibold text-midnight tracking-tight mb-4">
                Why Study Retention in Indian E-Commerce?
              </h3>

              <p className="text-sm text-text-secondary leading-relaxed mb-4">
                In competitive digital retail, customer acquisition costs consistently exceed the cost of cultivating existing relationships. In India's diverse e-commerce ecosystem, customer defection is shaped by distinct structural factors—including Cash-on-Delivery (COD) trust thresholds, courier transit delays across Tier 2 and Tier 3 hubs, and acute festive discount elasticity.
              </p>

              <p className="text-sm text-text-secondary leading-relaxed mb-4">
                Traditional retention approaches rely on reactive customer service or blunt, generic promotional discounts. RetainIQ investigates how machine learning can transform unstructured purchase logs into proactive, customer-level intelligence.
              </p>

              <div className="space-y-2.5 pt-2">
                <div className="flex items-start gap-2.5 text-xs text-text-secondary">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
                  <span><strong>Granular Risk Analysis:</strong> Replaces aggregate monthly churn rates with account-specific friction scoring.</span>
                </div>
                <div className="flex items-start gap-2.5 text-xs text-text-secondary">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
                  <span><strong>Behavioral Alignment:</strong> Pairs RFM clustering with tree-based classification to protect high-LTV accounts.</span>
                </div>
                <div className="flex items-start gap-2.5 text-xs text-text-secondary">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
                  <span><strong>Explainable Support:</strong> Supplements probability estimates with auditable, rule-based recommendations.</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-border text-[11px] text-text-muted flex items-center justify-between">
              <span>BCA AI & ML Capstone Project</span>
              <span className="font-mono text-text-secondary">Snapshot: Dec 31, 2025</span>
            </div>
          </div>

          {/* Right Column: Problem Statement & Exploration Scope */}
          <div className="lg:col-span-6 rounded-xl bg-surface border border-border shadow-card p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono font-medium uppercase tracking-wider text-text-secondary mb-3">
                <Target className="w-4 h-4 text-text-secondary shrink-0" />
                <span>Problem Statement</span>
              </div>

              <h3 className="font-heading text-xl sm:text-2xl font-semibold text-midnight tracking-tight mb-4">
                The Analytical Challenge of Customer Defection
              </h3>

              <p className="text-sm text-text-secondary leading-relaxed mb-4">
                E-commerce platforms capture high-velocity transaction and delivery events, yet discovering which customer accounts are quietly entering defection trajectories remains a complex diagnostic hurdle.
              </p>

              <div className="p-4 rounded-lg bg-bg border border-border mb-5 text-xs space-y-2">
                <span className="font-heading font-semibold text-midnight uppercase text-[10.5px] block tracking-wider">
                  Core Research Questions Explored:
                </span>
                <ul className="space-y-1.5 text-text-secondary list-disc list-inside">
                  <li>Can historical purchasing cadence reliably predict inactivity over a future 90-day window?</li>
                  <li>How do logistics friction signals (e.g., delivery delay SLA breaches) correlate with customer attrition?</li>
                  <li>Can unsupervised clustering isolate high-spend loyalists from lapsed buyers to prevent wasted retention spend?</li>
                  <li>How can black-box classification probabilities be translated into transparent operational decision support?</li>
                </ul>
              </div>

              <p className="text-xs text-text-muted italic leading-relaxed">
                * Note: The project explores predictive modeling methodologies on a curated dataset. It does not claim to solve every operational failure or eliminate real-world market uncertainty.
              </p>
            </div>

            <div className="mt-6 pt-4 border-t border-border text-[11px] text-text-muted flex items-center justify-between">
              <span>Multi-Region Dataset</span>
              <span className="font-mono text-text-secondary">15 States • 22 Cities</span>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* SUBSECTION C: SEVEN PROJECT OBJECTIVES                    */}
        {/* ======================================================== */}
        <div className="mb-16 sm:mb-20">
          <div className="max-w-2xl mb-8">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-2">
              PROJECT SCOPE
            </span>
            <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-2">
              Key Project Objectives
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Seven structured engineering and research milestones accomplished throughout the capstone lifecycle.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {projectObjectives.map((obj, i) => {
              const Icon = obj.icon;
              return (
                <div
                  key={i}
                  className="p-4 sm:p-5 rounded-xl bg-surface border border-border shadow-subtle flex flex-col justify-between hover:border-slate-300 transition-colors"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-mono text-xs font-semibold text-text-secondary px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                        {obj.num}
                      </span>
                      <Icon className="w-4 h-4 text-text-secondary" />
                    </div>
                    <h4 className="font-heading font-semibold text-midnight text-sm mb-1.5 leading-snug">
                      {obj.title}
                    </h4>
                    <p className="text-xs text-text-secondary leading-relaxed">
                      {obj.desc}
                    </p>
                  </div>
                </div>
              );
            })}

            {/* Verification Seal Card */}
            <div className="p-4 sm:p-5 rounded-xl bg-midnight border border-slate-800 text-white shadow-subtle flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-semibold text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800">
                    AUDITED
                  </span>
                  <Award className="w-4 h-4 text-slate-300" />
                </div>
                <h4 className="font-heading font-semibold text-white text-sm mb-1.5 leading-snug">
                  100% Phase Verification
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  All 10 project milestones verified via 160 automated tests in the master test suite (<code className="text-slate-300 text-[10.5px]">test_all_phases.py</code>).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* SUBSECTION D: ACADEMIC SPECIFICATION PANEL                */}
        {/* ======================================================== */}
        <div className="rounded-xl bg-surface border border-border shadow-card p-6 sm:p-8 lg:p-10 mb-16 sm:mb-20">
          <div className="max-w-2xl mb-8">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-2">
              CANONICAL METADATA
            </span>
            <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-2">
              Academic Project Specifications
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Official academic registry metadata from the project's canonical specification documents.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Project Title</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1 leading-snug">
                Indian E-Commerce Customer Retention Intelligence System
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Platform Brand</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1">
                RetainIQ Intelligence Platform
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Academic Context</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1">
                BCA (AI & Machine Learning) Final Year Project
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Domain & Context</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1">
                Machine Learning • Indian E-Commerce
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Supervised Model</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1">
                Random Forest Configuration D (150 Trees, τ = 0.50)
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Unsupervised Model</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1">
                StandardScaler + KMeans Clustering (K = 5)
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Dataset Volume</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1">
                7,000 Customers • 84,225 Transaction Records
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-bg border border-border">
              <span className="text-[10px] uppercase font-mono font-medium text-text-muted block">Decision Architecture</span>
              <p className="font-heading font-semibold text-midnight text-xs mt-1">
                43 Input Features • 8 Deterministic Business Rules
              </p>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-border text-[11px] text-text-muted italic flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span>* All academic details verified against PROJECT_CONTEXT.md and PROJECT_HANDOFF.md.</span>
            <span className="font-mono text-text-secondary">Workspace: C:\customer churn retention system</span>
          </div>
        </div>

        {/* ======================================================== */}
        {/* SUBSECTION E: VERIFIED TECHNOLOGY STACK                   */}
        {/* ======================================================== */}
        <div className="mb-16 sm:mb-20">
          <div className="max-w-2xl mb-8">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-2">
              IMPLEMENTATION STACK
            </span>
            <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-2">
              Verified Technology Stack
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Every library, framework, and language actively employed in the RetainIQ codebase.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {techStack.map((tech, i) => {
              const Icon = tech.icon;
              return (
                <div
                  key={i}
                  className="p-5 rounded-xl bg-surface border border-border shadow-subtle flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-text-secondary" />
                        <span className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
                          {tech.layer}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-bg border border-border text-text-muted">
                        {tech.badge}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {tech.technologies.map((t, ti) => (
                        <span
                          key={ti}
                          className="px-2 py-0.5 text-xs font-mono font-medium rounded bg-slate-100 text-midnight border border-slate-200"
                        >
                          {t}
                        </span>
                      ))}
                    </div>

                    <p className="text-xs text-text-secondary leading-relaxed">
                      {tech.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ======================================================== */}
        {/* SUBSECTION F: SCOPE, ASSUMPTIONS & LIMITATIONS           */}
        {/* ======================================================== */}
        <div className="rounded-xl bg-amber-50/60 border border-amber-200/80 p-6 sm:p-8 lg:p-10 mb-16">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-amber-900 mb-2">
            <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
            <span>Academic Scope & Scientific Disclosures</span>
          </div>

          <h3 className="font-heading text-xl sm:text-2xl font-semibold text-midnight tracking-tight mb-4">
            Research Scope, Boundary Conditions & Limitations
          </h3>

          <p className="text-sm text-text-secondary leading-relaxed mb-6">
            In accordance with sound academic methodology, the scope, constraints, and operational boundaries of the RetainIQ system are explicitly stated:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-lg bg-white border border-amber-200/60 shadow-subtle space-y-1">
              <span className="font-heading font-semibold text-midnight block">Synthetic Data Modality</span>
              <p className="text-text-secondary leading-relaxed">
                The project utilizes a statistically realistic, referentially integrated synthetic dataset (7,000 customers). It is not connected to live external enterprise production feeds or real consumer identity records.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-white border border-amber-200/60 shadow-subtle space-y-1">
              <span className="font-heading font-semibold text-midnight block">Raw Uncalibrated Probabilities</span>
              <p className="text-text-secondary leading-relaxed">
                Random Forest outputs represent raw tree ensemble voting proportions, not calibrated Bayesian probabilities. Predictions are classified using the pre-registered decision cutoff of τ = 0.50.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-white border border-amber-200/60 shadow-subtle space-y-1">
              <span className="font-heading font-semibold text-midnight block">Decision-Support Prescriptions</span>
              <p className="text-text-secondary leading-relaxed">
                Retention recommendations serve as operational decision-support guidance for managers. The platform does not automate financial disbursements, initiate unsolicited customer messaging, or guarantee commercial retention lift.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-white border border-amber-200/60 shadow-subtle space-y-1">
              <span className="font-heading font-semibold text-midnight block">Evaluation Environment</span>
              <p className="text-text-secondary leading-relaxed">
                Evaluations reflect empirical distributions under simulated temporal conditions (Dec 31, 2025 cutoff). The system does not claim to establish verified commercial revenue uplift in live commercial environments.
              </p>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* CLOSING SECTION CALL-TO-ACTION BANNER                     */}
        {/* ======================================================== */}
        <div className="rounded-xl bg-midnight p-8 sm:p-10 text-white shadow-card border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-xl">
            <span className="px-2.5 py-1 text-xs font-mono font-medium rounded bg-slate-800 text-slate-300 border border-slate-700 inline-block mb-3">
              OPERATIONAL PLATFORM • READY FOR DEMONSTRATION
            </span>
            <h3 className="font-heading text-xl sm:text-2xl font-semibold tracking-tight mb-2 text-white">
              Ready to Explore the Employee Portal & Live Inferences?
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              The employee portal with real-time churn prediction, 5 RFM personas, and prescriptive retention actions is fully integrated and operational. Sign in with administrator-approved credentials.
            </p>
          </div>

          <Button
            variant="primary"
            size="lg"
            icon={ArrowRight}
            iconPosition="right"
            onClick={handleEmployeePortalClick}
            className="shrink-0 text-sm font-semibold"
          >
            Launch Employee Portal
          </Button>
        </div>
      </Container>
    </section>
  );
}
