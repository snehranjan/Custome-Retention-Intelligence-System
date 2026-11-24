import React, { useState } from "react";
import {
  BrainCircuit,
  Database,
  Cpu,
  GitBranch,
  Layers,
  ArrowRight,
  CheckCircle2,
  Sliders,
  ShieldCheck,
  AlertTriangle,
  Lightbulb,
  Sparkles,
  Zap,
  BarChart3,
  Server,
  Terminal,
  Activity,
  Send,
  Code2,
  Lock,
  Compass,
  FileText,
  Clock,
  ChevronRight,
  TrendingDown,
  RefreshCw,
  FolderTree,
} from "lucide-react";
import { Container } from "../components/ui/Container";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

/**
 * RetainIQ How It Works & Technical ML Architecture Section (Phase 8.3.4)
 * Section Anchor: id="how-it-works"
 * 
 * Provides:
 * 1. 6-Stage Interactive Machine Learning Workflow Journey:
 *    - Stage 01: Customer Data Collection (7,000 synthetic records, Dec 31, 2025 cutoff)
 *    - Stage 02: Data Preprocessing & Feature Engineering (ColumnTransformer, Log1p, Imputation, CorrelationPruner)
 *    - Stage 03: Intelligent Customer Segmentation (KMeans K=5, RFM StandardScaler, 5 Personas)
 *    - Stage 04: Random Forest Churn Prediction (150 trees, locked tau=0.50, 3 Risk Tiers)
 *    - Stage 05: Rule-Based Retention Recommendations (8 empirical business rules, priority scoring)
 *    - Stage 06: Analytics & Decision Support (POST /api/v1/customers/analyze, unified intelligence)
 * 2. Complete End-to-End Technical Architecture Blueprint:
 *    - 4 Architectural Tiers: Data, ML Inference Core, FastAPI Backend, React Presentation
 * 3. Phase 8.3.5 Academic Project Details Milestone Preview
 */
export function HowItWorks({ onOpenActionModal }) {
  const [activeStage, setActiveStage] = useState(0);
  const [viewMode, setViewMode] = useState("workflow"); // 'workflow' | 'architecture'

  // Six Verified Technical Workflow Stages
  const workflowStages = [
    {
      id: 0,
      step: "01",
      title: "Data Collection & Partitioning",
      shortTitle: "Data Ingestion",
      category: "Data Engineering",
      icon: Database,
      tag: "OBSERVATION SNAPSHOT",
      tagColor: "bg-blue-100 text-blue-800 border-blue-200",
      summary:
        "The system ingests a rigorously structured synthetic Indian e-commerce dataset spanning 7,000 customer accounts and 84,225 transaction records with a strict observation cutoff date.",
      details: [
        {
          label: "Temporal Partitioning",
          value: "Dec 31, 2025 Cutoff",
          desc: "All predictive behavioral features are computed strictly from historical transactions prior to midnight Dec 31, 2025 to guarantee zero data leakage.",
        },
        {
          label: "Ground-Truth Churn Window",
          value: "Jan 1 – Mar 31, 2026 (90 Days)",
          desc: "Target label (churn=1) is assigned if an account placed zero delivered orders during the 90-day future evaluation window (3,207 churned vs 3,793 retained).",
        },
        {
          label: "Multi-Region Coverage",
          value: "15 States, 22 Major Hubs",
          desc: "Captures realistic geographic diversity across Tier 1 metropolitan areas and Tier 2 growth centers throughout India.",
        },
      ],
      codeSnippet: `// data/raw/customers.csv & orders.csv
{
  "customer_id": "IND_CUST_10001",
  "signup_date": "2024-04-12",
  "city": "Bengaluru",
  "state": "Karnataka",
  "snapshot_date": "2025-12-31",
  "churn": 0 // 1 if 0 delivered orders in Q1 2026
}`,
      provenance: "data/raw/customers.csv • backend/ml/validate_data.py",
    },
    {
      id: 1,
      step: "02",
      title: "Preprocessing & Advanced Features",
      shortTitle: "Feature Pipeline",
      category: "Feature Engineering",
      icon: Sliders,
      tag: "43 RAW FEATURES",
      tagColor: "bg-cyan-100 text-cyan-800 border-cyan-200",
      summary:
        "Raw transactional logs are transformed into 43 verified model inputs (40 numerical + 3 categorical) through an automated ColumnTransformer pipeline with custom correlation pruning.",
      details: [
        {
          label: "Log1p Transformation",
          value: "7 Skewed Monetary/Recency Columns",
          desc: "Applies log(1 + x) to highly skewed monetary spend, AOV, and recency days to normalize input distributions.",
        },
        {
          label: "Median Imputation & Indicators",
          value: "SimpleImputer(strategy='median', add_indicator=True)",
          desc: "Handles missing delivery delays and discount values while preserving explicit missingness indicators for zero-delivered accounts.",
        },
        {
          label: "Within-Fold Correlation Pruning",
          value: "CorrelationPruner(threshold=0.85)",
          desc: "Eliminates redundant collinear features within training folds, preventing variance inflation across momentum indicators.",
        },
      ],
      codeSnippet: `ColumnTransformer([
  ('num', Pipeline([
    ('log1p', Log1pTransformer()),
    ('imputer', SimpleImputer(strategy='median', add_indicator=True)),
    ('pruner', CorrelationPruner(threshold=0.85))
  ]), 40_numerical_cols),
  ('cat', Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
  ]), ['city', 'state', 'cluster_id'])
])`,
      provenance: "backend/ml/advanced_feature_engineering.py • models/phase5_1",
    },
    {
      id: 2,
      step: "03",
      title: "Intelligent RFM Segmentation",
      shortTitle: "RFM Segmentation",
      category: "Unsupervised Clustering",
      icon: Layers,
      tag: "K-MEANS (K=5)",
      tagColor: "bg-purple-100 text-purple-800 border-purple-200",
      summary:
        "Customers are clustered into five official behavioral personas using pre-fitted StandardScaler and KMeans (K=5) on log-transformed Recency, Frequency, and Monetary (RFM) distributions.",
      details: [
        {
          label: "Unsupervised RFM Clustering",
          value: "KMeans(n_clusters=5, random_state=42)",
          desc: "Pre-trained scaler and cluster centroids isolate distinct customer behaviors with high stability (Mean ARI = 0.9931 across random seeds).",
        },
        {
          label: "Zero-Delivered Isolation",
          value: "Cluster 2 (100% Purity)",
          desc: "Cleanly isolates accounts with zero fulfilled orders (484 customers, 76.2% observed churn) to apply specialized first-order activation.",
        },
        {
          label: "Feature Pipeline Feedback",
          value: "cluster_id Fed into Churn Model",
          desc: "The assigned cluster persona is supplied as a categorical feature to the downstream Random Forest classifier.",
        },
      ],
      codeSnippet: `// models/kmeans_customer_segmentation.joblib
const RFM_PERSONAS = {
  0: "Champions & High-Value Loyalists",      // 22.4% (₹1,13,448 spend)
  1: "At-Risk / Lapsed Low-Value Customers",  // 24.6% (66.9% churn)
  2: "Zero Delivered-Purchase Customers",     // 6.9%  (76.2% churn)
  3: "Steady Core Repeaters",                 // 28.6% (₹39,265 spend)
  4: "Recent Low-Ticket / New Promising Customers" // 17.5% (15d cadence)
};`,
      provenance: "models/kmeans_customer_segmentation.joblib • models/segmentation_scaler.joblib",
    },
    {
      id: 3,
      step: "04",
      title: "Random Forest Churn Prediction",
      shortTitle: "Churn Inference",
      category: "Supervised Classification",
      icon: BrainCircuit,
      tag: "LOCKED τ = 0.50",
      tagColor: "bg-rose-100 text-rose-800 border-rose-200",
      summary:
        "The locked production Random Forest pipeline evaluates customer risk against a strict mathematical decision threshold (τ = 0.50), mapping raw ensemble voting probabilities to three operational tiers.",
      details: [
        {
          label: "Ensemble Architecture",
          value: "150 Trees, Max Depth 8, Balanced",
          desc: "Trained on 5,950 development records (RandomForestClassifier, min_samples_leaf=5, class_weight='balanced') to maximize recall without overfitting.",
        },
        {
          label: "Locked Binary Threshold",
          value: "Cutoff τ = 0.50",
          desc: "p ≥ 0.50 assigns predicted Class 1 (Churn), while p < 0.50 assigns Class 0 (Retained). Standardized and immutable; no post-hoc adjustment.",
        },
        {
          label: "Operational Risk Tiers",
          value: "Low (< 0.50), Moderate (0.50–0.70), High (≥ 0.70)",
          desc: "Translates raw tree voting scores into targeted urgency tiers for operational dispatch. Raw tree probabilities are not calibrated.",
        },
      ],
      codeSnippet: `// models/phase5_1/final_model/final_churn_rf_pipeline.joblib
// SHA-256: 24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301
const prob = pipeline.predict_proba(features_df)[0][1];
const isChurn = prob >= 0.50; // tau = 0.50
const riskTier = prob >= 0.70 ? "HIGH" : 
                 prob >= 0.50 ? "MODERATE" : "LOW";`,
      provenance: "backend/app/services/churn_service.py • models/phase5_1/final_model/",
    },
    {
      id: 4,
      step: "05",
      title: "Explainable Retention Recommendations",
      shortTitle: "Rule Engine",
      category: "Decision Support",
      icon: Lightbulb,
      tag: "8 EMPIRICAL RULES",
      tagColor: "bg-amber-100 text-amber-800 border-amber-200",
      summary:
        "An auditable, deterministic business-rule engine inspects empirical friction signals, persona assignments, and risk scores to prescribe prioritized, explainable retention actions.",
      details: [
        {
          label: "Rule-Based Determinism",
          value: "8 Empirical Trigger Conditions",
          desc: "Evaluates SLA delivery breaches, recency decay, discount elasticity, cancellation rates, and loyalist spend thresholds without black-box opacity.",
        },
        {
          label: "Prescriptive Explanations",
          value: "Action + Reason + Evidence",
          desc: "Every intervention records its exact triggering condition (e.g., 'Avg delay 5.2 days exceeds 3.0d SLA limit') for complete managerial auditability.",
        },
        {
          label: "Multi-Channel Guidance",
          value: "WhatsApp SMS, Email Concierge",
          desc: "Recommends appropriate operational outreach channels based on customer tier and urgency without claiming automated payment execution.",
        },
      ],
      codeSnippet: `// backend/app/services/retention_service.py
if (features.avg_delivery_delay_days >= 3.0 || features.delay_friction_score >= 1.0) {
  recs.push({
    category: "Delivery Experience",
    suggested_action: "Prioritize courier dispatch to Express SLA & issue courtesy credit.",
    reason: "Repeated carrier delivery delays beyond SLA window elevate churn risk.",
    evidence: \`Average delay: \${avg_delay} days, Delay score: \${delay_score}\`,
    priority: "HIGH"
  });
}`,
      provenance: "backend/app/services/retention_service.py • Phase 7.3 Certified",
    },
    {
      id: 5,
      step: "06",
      title: "Unified Analytics & API Coordination",
      shortTitle: "Analytics & API",
      category: "Integration & Delivery",
      icon: BarChart3,
      tag: "REST API + UI",
      tagColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
      summary:
        "FastAPI service coordinators synthesize model predictions, RFM segmentation, and retention rules into unified responses, feeding the RetainIQ dashboard and cohort explorer.",
      details: [
        {
          label: "Unified Coordinator Endpoint",
          value: "POST /api/v1/customers/analyze",
          desc: "Single REST API call executes segmentation, feature alignment, Random Forest scoring, and rule evaluation with Pydantic validation.",
        },
        {
          label: "Enterprise Security Architecture",
          value: "ES256 JWKS Supabase Auth",
          desc: "Asymmetric public key cryptography verifies JWT tokens in FastAPI without shared database secrets. (Employee UI preview for Phase 8.4).",
        },
        {
          label: "Macro-to-Micro Exploration",
          value: "Cohort Filtering & Diagnostics",
          desc: "Enables retention managers to drill down from regional cohort metrics (7,000 accounts) to individual customer friction timelines.",
        },
      ],
      codeSnippet: `// POST /api/v1/customers/analyze
{
  "success": true,
  "data": {
    "segmentation": { "cluster_id": 0, "persona_name": "Champions & High-Value Loyalists" },
    "prediction": { "churn_probability": 0.764, "risk_tier": "HIGH" },
    "recommendations": { "top_priority": "HIGH", "total_recommendations": 2 }
  }
}`,
      provenance: "backend/app/services/customer_analysis_service.py • backend/app/main.py",
    },
  ];

  const currentStage = workflowStages[activeStage];

  const handleNextStage = () => {
    setActiveStage((prev) => (prev < workflowStages.length - 1 ? prev + 1 : 0));
  };

  const handlePrevStage = () => {
    setActiveStage((prev) => (prev > 0 ? prev - 1 : workflowStages.length - 1));
  };

  const handleAcademicDetailsClick = () => {
    const el = document.getElementById("about");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    } else if (onOpenActionModal) {
      onOpenActionModal({
        title: "Academic Project Details & Viva Prep",
        subtitle: "Phase 8.3.5 Milestone",
        message:
          "The Academic Project Details section is scheduled for Phase 8.3.5. It covers university capstone documentation, formal problem formulation, mathematical notations, and viva presentation assets.",
        icon: FileText,
      });
    }
  };

  return (
    <section
      id="how-it-works"
      className="relative py-16 sm:py-24 lg:py-28 bg-bg border-t border-border scroll-mt-20 overflow-hidden"
    >
      <Container size="default" className="relative z-10">
        {/* ======================================================== */}
        {/* SECTION HEADER                                            */}
        {/* ======================================================== */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-12 sm:mb-16">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-4">
            <Cpu className="w-3.5 h-3.5 text-electric shrink-0" />
            <span>ML PIPELINE & ARCHITECTURE</span>
          </div>

          <h2 className="font-heading text-3xl sm:text-4xl font-semibold text-midnight tracking-tight leading-tight mb-3">
            From Customer Data to Retention Intelligence
          </h2>

          <p className="text-base text-text-secondary leading-relaxed font-normal max-w-2xl mb-8">
            A structured machine-learning workflow that transforms customer behaviour into meaningful retention insights.
          </p>

          {/* View Mode Toggle: Workflow Stages vs Architecture Blueprint */}
          <div className="inline-flex p-1 rounded-lg bg-surface border border-border gap-1 text-xs font-medium">
            <button
              onClick={() => setViewMode("workflow")}
              className={`px-4 py-2 rounded-md transition-colors flex items-center gap-2 ${
                viewMode === "workflow"
                  ? "bg-midnight text-white"
                  : "text-text-secondary hover:text-midnight"
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              <span>6-Stage Workflow Journey</span>
            </button>
            <button
              onClick={() => setViewMode("architecture")}
              className={`px-4 py-2 rounded-md transition-colors flex items-center gap-2 ${
                viewMode === "architecture"
                  ? "bg-midnight text-white"
                  : "text-text-secondary hover:text-midnight"
              }`}
            >
              <FolderTree className="w-3.5 h-3.5" />
              <span>System Architecture Blueprint</span>
            </button>
          </div>
        </div>

        {/* ======================================================== */}
        {/* VIEW MODE 1: 6-STAGE WORKFLOW JOURNEY                     */}
        {/* ======================================================== */}
        {viewMode === "workflow" && (
          <div>
            {/* Horizontal Stage Stepper Bar */}
            <div className="mb-10 overflow-x-auto pb-2 scrollbar-thin">
              <div className="flex items-center justify-between min-w-[700px] border-b border-border pb-4">
                {workflowStages.map((stage, idx) => {
                  const isActive = activeStage === idx;
                  const isPast = activeStage > idx;
                  const Icon = stage.icon;

                  return (
                    <button
                      key={stage.id}
                      onClick={() => setActiveStage(idx)}
                      className={`flex flex-col items-center group relative px-3 py-2 rounded-lg transition-colors text-center ${
                        isActive
                          ? "bg-slate-100 text-electric font-semibold"
                          : "text-text-secondary hover:text-midnight hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <div
                          className={`w-7 h-7 rounded-md flex items-center justify-center text-xs font-mono font-medium transition-colors ${
                            isActive
                              ? "bg-electric text-white"
                              : isPast
                              ? "bg-slate-700 text-white"
                              : "bg-slate-100 text-text-muted border border-border"
                          }`}
                        >
                          {isPast ? <CheckCircle2 className="w-4 h-4" /> : stage.step}
                        </div>
                        <Icon className={`w-4 h-4 ${isActive ? "text-electric" : "text-text-muted"}`} />
                      </div>
                      <span className="text-xs font-heading tracking-tight whitespace-nowrap">
                        {stage.shortTitle}
                      </span>

                      {/* Active Indicator Underline */}
                      {isActive && (
                        <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-electric rounded-full" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Active Stage Content Card (2 Columns) */}
            <div className="rounded-xl bg-surface border border-border shadow-card p-6 sm:p-8 mb-12">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
                {/* Left Column: Stage Explanation & Verification */}
                <div className="lg:col-span-6 flex flex-col items-start">
                  <div className="flex items-center gap-2.5 mb-3 flex-wrap">
                    <span className="px-2 py-0.5 text-xs font-mono font-medium rounded bg-slate-900 text-white">
                      STAGE {currentStage.step} OF 06
                    </span>
                    <span className={`px-2 py-0.5 text-[10px] font-mono font-medium rounded border ${currentStage.tagColor}`}>
                      {currentStage.tag}
                    </span>
                    <span className="text-xs text-text-muted font-medium">
                      • {currentStage.category}
                    </span>
                  </div>

                  <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-3">
                    {currentStage.title}
                  </h3>

                  <p className="text-sm sm:text-base text-text-secondary leading-relaxed mb-6">
                    {currentStage.summary}
                  </p>

                  {/* Key Implementation Points */}
                  <div className="space-y-3 w-full mb-6">
                    {currentStage.details.map((item, i) => (
                      <div
                        key={i}
                        className="p-3.5 rounded-lg bg-bg border border-border flex flex-col gap-1 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-heading font-semibold text-midnight text-xs">
                            {item.label}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-surface border border-border text-electric font-mono text-[10.5px]">
                            {item.value}
                          </span>
                        </div>
                        <p className="text-text-secondary text-xs leading-relaxed mt-0.5">
                          {item.desc}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Provenance Footnote */}
                  <div className="p-3 rounded-lg bg-surface border border-border text-xs text-text-secondary w-full flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Code2 className="w-3.5 h-3.5 text-electric shrink-0" />
                      <span className="font-mono text-[11px] text-midnight">{currentStage.provenance}</span>
                    </div>
                    <span className="text-[11px] text-success font-medium flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                    </span>
                  </div>
                </div>

                {/* Right Column: Code/Pipeline Visual Mockup */}
                <div className="lg:col-span-6 flex flex-col h-full">
                  <div className="rounded-xl bg-midnight border border-slate-800 shadow-card overflow-hidden flex flex-col h-full">
                    {/* Terminal Header */}
                    <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
                          <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                        </div>
                        <span className="font-mono text-[11px] text-slate-300 ml-2">
                          retainiq-{currentStage.shortTitle.toLowerCase().replace(/\s+/g, "-")}.json
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-300 border border-slate-700">
                        Phase 7/8 Certified
                      </span>
                    </div>

                    {/* Code Display Body */}
                    <div className="p-5 font-mono text-xs text-slate-200 bg-midnight flex-grow overflow-x-auto leading-relaxed">
                      <pre className="text-[11.5px] whitespace-pre-wrap">{currentStage.codeSnippet}</pre>
                    </div>

                    {/* Diagnostic Context Bar */}
                    <div className="p-3 bg-slate-900/60 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Terminal className="w-3.5 h-3.5 text-slate-400" />
                        <span>Execution Pipeline: Zero Data Leakage Verified</span>
                      </span>
                      <span className="text-slate-400 font-mono">Step {currentStage.step}/06</span>
                    </div>
                  </div>

                  {/* Stage Stepper Controls */}
                  <div className="flex items-center justify-between gap-3 mt-4 pt-3 border-t border-border">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handlePrevStage}
                      className="text-xs"
                    >
                      ← Previous Stage
                    </Button>
                    <span className="text-xs text-text-muted font-medium">
                      Stage {activeStage + 1} of {workflowStages.length}
                    </span>
                    <Button
                      variant="primary"
                      size="sm"
                      icon={ArrowRight}
                      iconPosition="right"
                      onClick={handleNextStage}
                      className="text-xs"
                    >
                      Next Stage →
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* VIEW MODE 2: END-TO-END ARCHITECTURE BLUEPRINT            */}
        {/* ======================================================== */}
        {viewMode === "architecture" && (
          <div className="rounded-xl bg-surface border border-border shadow-card p-6 sm:p-8 mb-12">
            <div className="max-w-2xl mb-8">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-2">
                VERIFIED TECHNICAL BLUEPRINT
              </span>
              <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-2">
                End-to-End System Architecture
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                A decoupled, modular architecture connecting raw transaction datasets, scikit-learn machine learning pipelines, FastAPI REST services, and the RetainIQ analytics interface.
              </p>
            </div>

            {/* 4-Tier Architecture Diagram Grid */}
            <div className="space-y-4">
              {/* TIER 1: DATA INGESTION & STORAGE LAYER */}
              <div className="p-4 sm:p-5 rounded-lg bg-bg border border-border relative">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-text-secondary" />
                    <span className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
                      Tier 1 • Data Storage & Ingestion Layer
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                    Dec 31, 2025 Snapshot Cutoff
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <span className="font-heading font-semibold text-midnight block">customers.csv (N=7,000)</span>
                    <span className="text-text-muted text-[11px] block mt-0.5">Demographics, signup date, city, state across 15 Indian states.</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <span className="font-heading font-semibold text-midnight block">orders.csv (N=84,225)</span>
                    <span className="text-text-muted text-[11px] block mt-0.5">Historical orders, delivery SLA delay, payment method, discount INR.</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <span className="font-heading font-semibold text-midnight block">SQLite Storage Fallback</span>
                    <span className="text-text-muted text-[11px] block mt-0.5">Local database with Supabase PostgreSQL cloud sync architecture.</span>
                  </div>
                </div>
              </div>

              {/* Directional Connector */}
              <div className="flex justify-center text-text-muted text-xs">
                <span className="px-3 py-1 rounded-full bg-surface border border-border font-mono text-[10px] text-text-secondary flex items-center gap-1">
                  ↓ Preprocessing & Feature Extraction (43 Raw Columns)
                </span>
              </div>

              {/* TIER 2: MACHINE LEARNING INFERENCE CORE */}
              <div className="p-4 sm:p-5 rounded-lg bg-bg border border-border relative">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <BrainCircuit className="w-4 h-4 text-text-secondary" />
                    <span className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
                      Tier 2 • Machine Learning Inference Core (Phase 5.1 Certified)
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-rose-600 font-semibold">
                    Locked τ = 0.50
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-heading font-semibold text-midnight">ColumnTransformer</span>
                      <span className="text-[10px] font-mono text-text-muted">43 Inputs</span>
                    </div>
                    <span className="text-text-muted text-[11px] block">Log1p on monetary spend + SimpleImputer + CorrelationPruner (0.85) + OneHotEncoder.</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-heading font-semibold text-midnight">KMeans Segmentation</span>
                      <span className="text-[10px] font-mono text-purple-600">K = 5</span>
                    </div>
                    <span className="text-text-muted text-[11px] block">StandardScaler on log(1+RFM) assigning 5 official personas. Mean ARI = 0.9931.</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-heading font-semibold text-midnight">Random Forest Pipeline</span>
                      <span className="text-[10px] font-mono text-danger">150 Trees</span>
                    </div>
                    <span className="text-text-muted text-[11px] block">Max depth 8, balanced class weights, locked tau=0.50 threshold, 3 risk tiers.</span>
                  </div>
                </div>
              </div>

              {/* Directional Connector */}
              <div className="flex justify-center text-text-muted text-xs">
                <span className="px-3 py-1 rounded-full bg-surface border border-border font-mono text-[10px] text-text-secondary flex items-center gap-1">
                  ↓ REST Endpoints & Service Coordination
                </span>
              </div>

              {/* TIER 3: FASTAPI BACKEND & SERVICES */}
              <div className="p-4 sm:p-5 rounded-lg bg-bg border border-border relative">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Server className="w-4 h-4 text-text-secondary" />
                    <span className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
                      Tier 3 • FastAPI REST Service Layer (Uvicorn Port 8000)
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-success font-semibold">
                    OpenAPI v3 Validated
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-surface border border-border">
                    <span className="font-heading font-semibold text-midnight block text-[11px]">ChurnPredictionService</span>
                    <span className="text-text-muted text-[10.5px] block mt-0.5">POST /api/v1/predictions/churn with 43-feature DataFrame inference.</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-border">
                    <span className="font-heading font-semibold text-midnight block text-[11px]">CustomerSegmentationService</span>
                    <span className="text-text-muted text-[10.5px] block mt-0.5">POST /api/v1/segmentation/predict with RFM persona assignment.</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-border">
                    <span className="font-heading font-semibold text-midnight block text-[11px]">RetentionRecommendationEngine</span>
                    <span className="text-text-muted text-[10.5px] block mt-0.5">POST /api/v1/retention/recommendations with 8 business rules.</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface border border-border">
                    <span className="font-heading font-semibold text-midnight block text-[11px]">CustomerAnalysisService</span>
                    <span className="text-text-muted text-[10.5px] block mt-0.5">POST /api/v1/customers/analyze unifying all 3 core capabilities.</span>
                  </div>
                </div>
              </div>

              {/* Directional Connector */}
              <div className="flex justify-center text-text-muted text-xs">
                <span className="px-3 py-1 rounded-full bg-surface border border-border font-mono text-[10px] text-text-secondary flex items-center gap-1">
                  ↓ JSON Response Payloads & Auth Session Tokens
                </span>
              </div>

              {/* TIER 4: CLIENT PRESENTATION LAYER */}
              <div className="p-4 sm:p-5 rounded-lg bg-bg border border-border relative">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-text-secondary" />
                    <span className="font-heading font-semibold text-xs uppercase tracking-wider text-midnight">
                      Tier 4 • RetainIQ React 19 Frontend (Vite + Tailwind)
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-electric font-semibold">
                    Port 5173 Live
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-heading font-semibold text-midnight">Public Landing Experience (Phase 8.3)</span>
                      <span className="px-2 py-0.5 text-[9px] font-heading font-semibold rounded bg-success/10 text-success">Active</span>
                    </div>
                    <span className="text-text-muted text-[11px] block">Hero Section, Platform Highlights, Feature Deep-Dive, and Technical Architecture.</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface border border-border">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-heading font-semibold text-midnight">Employee Intelligence Portal (Phase 8.4)</span>
                      <span className="px-2 py-0.5 text-[9px] font-heading font-semibold rounded bg-slate-100 text-slate-700 border border-slate-200">Active</span>
                    </div>
                    <span className="text-text-muted text-[11px] block">Supabase JWT employee login, live prediction explorer, and cohort analytics dashboard.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* CLOSING SECTION TRANSITION BANNER (PHASE 8.3.5 PREVIEW)  */}
        {/* ======================================================== */}
        <div className="rounded-xl bg-midnight p-8 sm:p-10 text-white shadow-card border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-xl">
            <span className="px-2.5 py-1 text-xs font-mono font-medium rounded bg-slate-800 text-slate-300 border border-slate-700 inline-block mb-3">
              ACADEMIC CAPSTONE • RESEARCH & METHODOLOGY
            </span>
            <h3 className="font-heading text-xl sm:text-2xl font-semibold tracking-tight mb-2 text-white">
              Interested in the Academic Research & Methodology Details?
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Explore the formal problem formulation, mathematical notations, experimental benchmarking history, and university capstone presentation assets.
            </p>
          </div>

          <Button
            variant="primary"
            size="lg"
            icon={ArrowRight}
            iconPosition="right"
            onClick={handleAcademicDetailsClick}
            className="shrink-0 text-sm font-semibold"
          >
            Preview Academic Details
          </Button>
        </div>
      </Container>
    </section>
  );
}
