import React, { useState } from "react";
import {
  BrainCircuit,
  Users,
  Lightbulb,
  BarChart3,
  ShieldCheck,
  TrendingDown,
  ArrowRight,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Activity,
  Send,
  Sliders,
  Compass,
  FileText,
  Clock,
  ShieldAlert,
  ChevronRight,
  CornerDownRight,
} from "lucide-react";
import { Container } from "../components/ui/Container";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

/**
 * RetainIQ Feature Showcase & Deep-Dive Section (Phase 8.3.3)
 * Positioned immediately after Platform Highlights with anchor id="features".
 * Provides four comprehensive, in-depth feature showcases:
 * 1. Intelligent Churn Prediction (43 features, Random Forest, locked tau = 0.50)
 * 2. Customer Segmentation Intelligence (5 official RFM personas, K=5)
 * 3. Intelligent Retention Recommendations (explainable, prioritized rule engine)
 * 4. Actionable Customer Analytics (cohort distribution, KPI metrics)
 */
export function FeatureShowcase({ onOpenActionModal }) {
  const [activeSegmentTab, setActiveSegmentTab] = useState(0);

  // 5 Official Project Segments (Strictly Preserved)
  const officialSegments = [
    {
      id: 0,
      name: "Champions & High-Value Loyalists",
      cluster: "Cluster 0",
      description: "Highest customer lifetime value, frequent purchases, and strong brand engagement. Retention focus is VIP relationship preservation.",
      color: "border-purple-200 bg-purple-50 text-purple-700",
      badgeBg: "bg-purple-100 text-purple-800",
      stats: { avgSpend: "₹1,13,448", orderCadence: "13 days", churnRate: "19.6%" },
    },
    {
      id: 1,
      name: "At-Risk / Lapsed Low-Value Customers",
      cluster: "Cluster 1",
      description: "Extended recency drift (>90 days), steep velocity decay, and reduced order momentum requiring targeted win-back re-engagement.",
      color: "border-amber-200 bg-amber-50 text-amber-700",
      badgeBg: "bg-amber-100 text-amber-800",
      stats: { avgSpend: "₹5,725", orderCadence: "275 days", churnRate: "66.9%" },
    },
    {
      id: 2,
      name: "Zero Delivered-Purchase Customers",
      cluster: "Cluster 2",
      description: "Shoppers with cart checkout attempts or cancellations but zero completed deliveries. Primary focus is initial platform fulfillment trust.",
      color: "border-rose-200 bg-rose-50 text-rose-700",
      badgeBg: "bg-rose-100 text-rose-800",
      stats: { avgSpend: "₹0", orderCadence: "No Delivery", churnRate: "76.2%" },
    },
    {
      id: 3,
      name: "Steady Core Repeaters",
      cluster: "Cluster 3",
      description: "Consistent and dependable recurring purchasers with stable momentum and moderate ticket size across essential product categories.",
      color: "border-blue-200 bg-blue-50 text-blue-700",
      badgeBg: "bg-blue-100 text-blue-800",
      stats: { avgSpend: "₹39,265", orderCadence: "76 days", churnRate: "43.0%" },
    },
    {
      id: 4,
      name: "Recent Low-Ticket / New Promising Customers",
      cluster: "Cluster 4",
      description: "Newly acquired accounts with recent low-value transactions exhibiting promising reorder potential if nurtured effectively.",
      color: "border-emerald-200 bg-emerald-50 text-emerald-700",
      badgeBg: "bg-emerald-100 text-emerald-800",
      stats: { avgSpend: "₹10,695", orderCadence: "15 days", churnRate: "42.4%" },
    },
  ];

  const handleTechArchitectureClick = () => {
    const el = document.getElementById("how-it-works");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    } else if (onOpenActionModal) {
      onOpenActionModal({
        title: "Technical Architecture & How It Works",
        subtitle: "Phase 8.3.4 Milestone",
        message:
          "The comprehensive ML Architecture and How It Works section is scheduled for Phase 8.3.4. It covers the 43-feature pipeline, Random Forest Configuration D, KMeans clustering, and FastAPI JWKS verification in technical detail.",
        icon: BrainCircuit,
      });
    }
  };

  return (
    <section
      id="features"
      className="relative py-14 sm:py-20 lg:py-24 bg-bg border-t border-border/80 scroll-mt-20"
    >
      <Container size="default" className="relative z-10">
        {/* ======================================================== */}
        {/* SECTION INTRODUCTION                                      */}
        {/* ======================================================== */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-12 sm:mb-18">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface border border-border text-xs font-mono text-text-secondary mb-3 shadow-subtle">
            <span className="w-1.5 h-1.5 rounded-full bg-electric" />
            <span>Core Capabilities in Depth</span>
          </div>

          <h2 className="font-heading text-2xl sm:text-3xl md:text-4xl font-semibold text-midnight tracking-tight leading-tight mb-3">
            A Closer Look at RetainIQ
          </h2>

          <p className="text-sm sm:text-base text-text-secondary leading-relaxed font-normal max-w-2xl">
            Explore how customer telemetry, supervised machine learning, and prescriptive retention actions operate across the platform.
          </p>
        </div>

        {/* ======================================================== */}
        {/* FEATURE 01 — INTELLIGENT CHURN PREDICTION ENGINE          */}
        {/* ======================================================== */}
        <div className="mb-16 sm:mb-24 lg:mb-28">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
            {/* Left Column: Text & Architecture Explanation */}
            <div className="lg:col-span-6 flex flex-col items-start">
              <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono text-text-secondary bg-surface border border-border mb-2.5">
                <BrainCircuit className="w-3.5 h-3.5 text-electric" strokeWidth={1.75} />
                <span>Feature 01 • Predictive Intelligence</span>
              </div>

              <h3 className="font-heading text-xl sm:text-2xl font-semibold text-midnight tracking-tight mb-3">
                Customer-Level Risk Scoring with Random Forest
              </h3>

              <p className="text-sm text-text-secondary leading-relaxed mb-5">
                RetainIQ evaluates 43 behavioral and transactional signals—including historical order cadence, 30/90-day velocity ratios, delivery delay friction, and return momentum—through a production Random Forest pipeline to identify accounts approaching churn.
              </p>

              {/* Architectural Feature Bullets */}
              <div className="space-y-2.5 mb-5 w-full">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded bg-surface-muted text-electric flex items-center justify-center shrink-0 mt-0.5 border border-border">
                    <Activity className="w-3.5 h-3.5" strokeWidth={1.75} />
                  </div>
                  <div>
                    <h4 className="font-heading text-xs font-semibold text-midnight">43 Behavioral Features Evaluated</h4>
                    <p className="text-[11px] text-text-secondary mt-0.5 leading-relaxed">
                      Captures Recency, Order Frequency, Delivery Delay Friction, Payment Methods, and 30-to-180 day velocity momentum.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-lg bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded bg-surface-muted text-navy flex items-center justify-center shrink-0 mt-0.5 border border-border">
                    <Sliders className="w-3.5 h-3.5" strokeWidth={1.75} />
                  </div>
                  <div>
                    <h4 className="font-heading text-xs font-semibold text-midnight">Locked Decision Threshold (τ = 0.50)</h4>
                    <p className="text-[11px] text-text-secondary mt-0.5 leading-relaxed">
                      Applies an uncompromised mathematical cutoff: churn probability p ≥ 0.50 assigns predicted Class 1 (Churn), while p &lt; 0.50 assigns Class 0 (Retained).
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-lg bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded bg-surface-muted text-danger flex items-center justify-center shrink-0 mt-0.5 border border-border">
                    <TrendingDown className="w-3.5 h-3.5" strokeWidth={1.75} />
                  </div>
                  <div>
                    <h4 className="font-heading text-xs font-semibold text-midnight">3 Operational Risk Tiers</h4>
                    <p className="text-[11px] text-text-secondary mt-0.5 leading-relaxed">
                      Categorizes accounts into Low (p &lt; 0.50), Moderate (0.50 ≤ p &lt; 0.70), and High Risk (p ≥ 0.70) for targeted operational intervention.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Illustrative Terminal & Prediction Preview */}
            <div className="lg:col-span-6">
              <div className="rounded-xl bg-surface border border-border shadow-card p-5 sm:p-6 relative overflow-hidden">
                <div className="flex items-center justify-between pb-3.5 mb-4 border-b border-border/80">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-danger shrink-0" />
                    <span className="font-heading text-xs sm:text-sm font-semibold text-midnight tracking-tight">
                      Customer Prediction Diagnostic
                    </span>
                  </div>
                  <span className="text-[10.5px] font-mono px-2 py-0.5 rounded bg-bg text-text-muted border border-border">
                    Illustrative Preview
                  </span>
                </div>

                {/* Account Profile Header */}
                <div className="p-3 rounded-lg bg-bg border border-border/80 mb-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs">
                  <div>
                    <span className="text-[10px] text-text-muted font-mono block">Account Identifier</span>
                    <div className="font-mono font-bold text-midnight text-xs sm:text-sm">
                      IND_CUST_4821 <span className="text-[10.5px] text-text-muted font-normal">(Sample Demonstration Account)</span>
                    </div>
                    <span className="text-text-secondary text-[11px] font-mono">Mumbai, Maharashtra • Cluster 1</span>
                  </div>
                  <div className="sm:text-right">
                    <span className="text-[10px] text-text-muted font-mono block">Model Decision</span>
                    <div>
                      <span className="inline-block px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-rose-50 text-rose-800 border border-rose-200">
                        Class 1 • Churn Risk
                      </span>
                    </div>
                  </div>
                </div>

                {/* Metric Readout & Risk Gauge */}
                <div className="p-3.5 rounded-lg bg-surface border border-border/80 mb-3.5 space-y-3">
                  <div className="flex items-baseline justify-between">
                    <div>
                      <span className="text-[10px] font-mono text-text-muted block">Raw Predicted Churn Score</span>
                      <span className="font-mono text-2xl sm:text-3xl font-semibold text-danger tabular-nums">78.4%</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-mono text-text-muted block">Risk Tier</span>
                      <Badge variant="high_risk" dot={true} size="sm">
                        High Risk (p ≥ 0.70)
                      </Badge>
                    </div>
                  </div>

                  {/* 3 Key Friction Signals */}
                  <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border/60">
                    <div className="p-2 rounded bg-bg border border-border">
                      <span className="text-[10px] text-text-muted block font-mono">Avg Delay</span>
                      <span className="font-mono font-semibold text-danger text-xs sm:text-sm tabular-nums">5.2 Days</span>
                      <span className="text-[9.5px] text-text-secondary block font-mono">SLA Breached</span>
                    </div>

                    <div className="p-2 rounded bg-bg border border-border">
                      <span className="text-[10px] text-text-muted block font-mono">Velocity 30/90d</span>
                      <span className="font-mono font-semibold text-amber-700 text-xs sm:text-sm tabular-nums">0.18 Ratio</span>
                      <span className="text-[9.5px] text-text-secondary block font-mono">Decay Drift</span>
                    </div>

                    <div className="p-2 rounded bg-bg border border-border">
                      <span className="text-[10px] text-text-muted block font-mono">Return Rate</span>
                      <span className="font-mono font-semibold text-midnight text-xs sm:text-sm tabular-nums">28.5%</span>
                      <span className="text-[9.5px] text-text-secondary block font-mono">Elevated</span>
                    </div>
                  </div>
                </div>

                {/* Academic Guardrail Footnote */}
                <div className="pt-2.5 border-t border-border/70 flex flex-col sm:flex-row items-center justify-between gap-1.5 text-[10px] text-text-muted font-mono">
                  <span>Binary Cutoff: <strong className="text-midnight font-bold">τ = 0.50</strong></span>
                  <span className="italic">* Raw ensemble votes; not Bayesian probabilities.</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* FEATURE 02 — CUSTOMER SEGMENTATION INTELLIGENCE (K=5)     */}
        {/* ======================================================== */}
        <div className="mb-20 sm:mb-24 lg:mb-28">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* Left Column: Interactive 5-Persona Explorer Preview */}
            <div className="lg:col-span-6 order-2 lg:order-1">
              <div className="rounded-xl bg-surface border border-border shadow-card p-5 sm:p-7">
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-text-secondary" />
                    <span className="font-heading text-xs sm:text-sm font-semibold text-midnight tracking-tight">
                      RFM Segmentation Matrix (K=5)
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-text-muted">
                    Segment Mapping Preview
                  </span>
                </div>

                {/* 5 Selectable Persona Tabs */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {officialSegments.map((seg, idx) => (
                    <button
                      key={seg.id}
                      onClick={() => setActiveSegmentTab(idx)}
                      className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-colors ${
                        activeSegmentTab === idx
                          ? "bg-midnight text-white border-midnight"
                          : "bg-surface text-text-secondary border-border hover:bg-bg hover:text-midnight"
                      }`}
                    >
                      {seg.cluster}
                    </button>
                  ))}
                </div>

                {/* Active Persona Deep-Dive Card */}
                {officialSegments[activeSegmentTab] && (
                  <div className="p-4 rounded-lg bg-bg border border-border mb-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                      <h4 className="font-heading font-semibold text-midnight text-sm sm:text-base">
                        {officialSegments[activeSegmentTab].name}
                      </h4>
                      <span className={`self-start sm:self-auto px-2 py-0.5 text-[10px] font-mono font-medium rounded border ${officialSegments[activeSegmentTab].color}`}>
                        {officialSegments[activeSegmentTab].cluster}
                      </span>
                    </div>

                    <p className="text-xs text-text-secondary leading-relaxed mb-4">
                      {officialSegments[activeSegmentTab].description}
                    </p>

                    {/* Empirical Cohort Metrics */}
                    <div className="grid grid-cols-3 gap-2 pt-3 border-t border-border text-center">
                      <div className="p-2 rounded-md bg-surface border border-border">
                        <span className="text-[10px] text-text-muted block">Avg Spend</span>
                        <span className="font-heading font-semibold text-xs sm:text-sm text-midnight tabular-nums">
                          {officialSegments[activeSegmentTab].stats.avgSpend}
                        </span>
                      </div>

                      <div className="p-2 rounded-md bg-surface border border-border">
                        <span className="text-[10px] text-text-muted block">Order Cadence</span>
                        <span className="font-heading font-semibold text-xs sm:text-sm text-midnight tabular-nums">
                          {officialSegments[activeSegmentTab].stats.orderCadence}
                        </span>
                      </div>

                      <div className="p-2 rounded-md bg-surface border border-border">
                        <span className="text-[10px] text-text-muted block">Avg Churn Rate</span>
                        <span className="font-heading font-semibold text-xs sm:text-sm text-danger tabular-nums">
                          {officialSegments[activeSegmentTab].stats.churnRate}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* 5-Persona Quick Reference List */}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-heading font-semibold text-text-muted uppercase tracking-wider block">
                    All 5 Official Segments (Standard Scaler + KMeans)
                  </span>
                  {officialSegments.map((seg, idx) => (
                    <div
                      key={seg.id}
                      onClick={() => setActiveSegmentTab(idx)}
                      className={`flex items-center justify-between p-2 rounded-lg cursor-pointer border text-xs transition-colors ${
                        activeSegmentTab === idx
                          ? "bg-surface border-electric shadow-subtle"
                          : "bg-surface/60 border-border/70 hover:bg-surface"
                      }`}
                    >
                      <span className="text-xs font-medium text-text-primary truncate">
                        {seg.name}
                      </span>
                      <span className="font-mono text-[11px] text-text-muted shrink-0 ml-2">
                        {seg.cluster}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="mt-4 pt-3 border-t border-border text-[10px] text-text-muted italic text-center">
                  * Empirical cluster metrics computed on 7,000 customer dataset (data/processed/cluster_profiles.csv). N=7,000.
                </div>
              </div>
            </div>

            {/* Right Column: Text & Methodology */}
            <div className="lg:col-span-6 order-1 lg:order-2 flex flex-col items-start">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-3">
                <Users className="w-3.5 h-3.5" />
                <span>Feature 02 • RFM Segmentation</span>
              </div>

              <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-4">
                Behavioral Cohort Intelligence Across 5 Segments
              </h3>

              <p className="text-base text-text-secondary leading-relaxed mb-6">
                Treating all churn risk uniformly leads to misallocated retention spend. RetainIQ clusters customers into five distinct personas derived from Recency, Frequency, and Monetary (RFM) distributions, ensuring interventions match customer value and purchasing history.
              </p>

              <div className="space-y-3 w-full">
                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">High-Value Loyalist Protection</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Cluster 0 accounts represent top lifetime spend (₹15,000+). Even slight delay signals trigger proactive concierge support to defend core revenue.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <Zap className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">First-Order Activation Strategy</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Cluster 2 accounts attempted purchases but suffered cancellations or fulfillment failures. Retention focuses on delivery assurance and COD trust.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">Lapsed Customer Momentum Recovery</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Cluster 1 accounts display severe recency decay. Win-back logic pairs velocity analysis with targeted re-engagement offers.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* FEATURE 03 — INTELLIGENT RETENTION RECOMMENDATIONS         */}
        {/* ======================================================== */}
        <div className="mb-20 sm:mb-24 lg:mb-28">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* Left Column: Text & Rule-Based Logic */}
            <div className="lg:col-span-6 flex flex-col items-start">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-3">
                <Lightbulb className="w-3.5 h-3.5" />
                <span>Feature 03 • Action Engine</span>
              </div>

              <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-4">
                Explainable, Rule-Based Retention Interventions
              </h3>

              <p className="text-base text-text-secondary leading-relaxed mb-6">
                Black-box predictions tell you who is leaving, but not how to keep them. RetainIQ pairs model outputs with an auditable rule engine that identifies primary friction drivers and prescribes targeted, high-priority retention actions.
              </p>

              <div className="space-y-3 w-full">
                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">Transparent Reason & Evidence Tracking</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Every prescription documents its underlying empirical evidence (e.g., SLA delay days, spend thresholds, cluster persona) for full auditability.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <Send className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">Multi-Channel Guidance</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Recommends specific, appropriate communication channels—such as WhatsApp delivery alerts, VIP concierge emails, or targeted re-engagement promos.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">Strict Academic & Operational Honesty</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Recommendations serve as decision-support guidance. The platform does not claim guaranteed retention lift or automated financial execution.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Prescriptive Recommendation Visual Mockup */}
            <div className="lg:col-span-6">
              <div className="rounded-xl bg-surface border border-border shadow-card p-5 sm:p-7">
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-text-secondary" />
                    <span className="font-heading text-xs sm:text-sm font-semibold text-midnight tracking-tight">
                      Prescriptive Intervention Card
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-text-muted">
                    Illustrative Recommendation Preview
                  </span>
                </div>

                {/* Target Customer Context */}
                <div className="p-3 rounded-lg bg-bg border border-border mb-4 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-[10px] text-text-muted uppercase font-heading">Target Customer</span>
                    <div className="font-heading font-semibold text-midnight">
                      <span className="font-mono">IND_CUST_1024</span> <span className="text-[10px] text-text-muted font-normal">(Demo Account)</span> • Bengaluru
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-text-muted uppercase font-heading block">Risk Tier</span>
                    <Badge variant="warning" size="sm" dot={true}>
                      Moderate (0.50 ≤ p &lt; 0.70)
                    </Badge>
                  </div>
                </div>

                {/* Prescribed Action Detail */}
                <div className="p-4 rounded-lg bg-surface border border-electric/30 shadow-subtle mb-4 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-[11px] font-semibold uppercase text-electric tracking-wide">
                      Prescribed Action (Priority: High)
                    </span>
                    <span className="px-2 py-0.5 font-mono text-[10px] rounded bg-slate-100 text-text-secondary border border-border">
                      Rule: Delivery SLA Breach
                    </span>
                  </div>

                  <div className="font-heading font-semibold text-midnight text-sm sm:text-base leading-snug">
                    Provide proactive ₹150 delivery inconvenience credit & upgrade courier dispatch to Express SLA.
                  </div>

                  <div className="text-xs text-text-secondary leading-relaxed pt-2 border-t border-border">
                    <strong className="text-text-primary">Diagnostic Reason:</strong> Customer experienced repeated SLA delivery breaches (avg delay 4.8 days) despite being in Cluster 0 (Champions & Loyalists). High lifetime spend (₹18,450) is at immediate risk.
                  </div>

                  <div className="p-2.5 rounded-lg bg-bg border border-border flex items-center justify-between text-xs">
                    <span className="text-text-muted text-[11px] font-medium">Suggested Outreach Channel</span>
                    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface border border-border text-electric font-medium text-[11px]">
                      <Send className="w-3 h-3" />
                      <span>Email Concierge & WhatsApp SMS</span>
                    </div>
                  </div>
                </div>

                {/* Academic Honesty Disclosure */}
                <div className="pt-3 border-t border-border text-[10px] text-text-muted italic text-center">
                  * Illustrative recommendation demonstrating rule engine logic. Does not promise financial lift or execute automated payments.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* FEATURE 04 — ACTIONABLE CUSTOMER ANALYTICS & COHORT VIEW */}
        {/* ======================================================== */}
        <div className="mb-20 sm:mb-24">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* Left Column: Analytics Dashboard Mockup */}
            <div className="lg:col-span-6 order-2 lg:order-1">
              <div className="rounded-xl bg-surface border border-border shadow-card p-5 sm:p-7">
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-text-secondary" />
                    <span className="font-heading text-xs sm:text-sm font-semibold text-midnight tracking-tight">
                      Cohort Analytics Console
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-text-muted">
                    Illustrative Sample Analytics
                  </span>
                </div>

                {/* KPI Metrics Summary Strip */}
                <div className="grid grid-cols-3 gap-2 mb-4">
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-[10px] font-heading font-medium text-text-muted block">Analyzed Cohort</span>
                    <span className="font-heading font-semibold text-lg sm:text-xl text-midnight block mt-0.5 tabular-nums">7,000</span>
                    <span className="text-[10px] text-text-secondary">Development records</span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-[10px] font-heading font-medium text-text-muted block">At-Risk Ratio</span>
                    <span className="font-heading font-semibold text-lg sm:text-xl text-danger block mt-0.5 tabular-nums">47.9%</span>
                    <span className="text-[10px] text-text-secondary">3,356 at p ≥ 0.50</span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-[10px] font-heading font-medium text-text-muted block">Decision Cutoff</span>
                    <span className="font-heading font-semibold text-lg sm:text-xl text-electric block mt-0.5 tabular-nums">τ = 0.50</span>
                    <span className="text-[10px] text-text-secondary">Binary threshold</span>
                  </div>
                </div>

                {/* Risk Distribution Proportional Bar */}
                <div className="p-3.5 rounded-lg bg-bg border border-border mb-4">
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="font-heading font-semibold text-midnight text-xs">
                      Population Risk Breakdown
                    </span>
                    <span className="font-mono text-[10px] text-text-muted">3 Operational Tiers</span>
                  </div>

                  <div className="h-2 w-full rounded bg-slate-200/80 flex overflow-hidden gap-0.5 mb-2.5">
                    <div className="h-full rounded-sm bg-success" style={{ width: "52.1%" }} title="Low: 52.1%" />
                    <div className="h-full rounded-sm bg-warning" style={{ width: "30.7%" }} title="Moderate: 30.7%" />
                    <div className="h-full rounded-sm bg-danger" style={{ width: "17.3%" }} title="High: 17.3%" />
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="p-1.5 rounded-md bg-surface border border-border">
                      <span className="text-[10px] text-text-muted block">Low (p &lt; 0.50)</span>
                      <strong className="text-midnight text-xs font-heading font-semibold tabular-nums">52.1%</strong>
                      <span className="text-[9px] text-text-muted block font-mono">3,644 acc</span>
                    </div>

                    <div className="p-1.5 rounded-md bg-surface border border-border">
                      <span className="text-[10px] text-text-muted block">Mod (0.50 ≤ p &lt; 0.70)</span>
                      <strong className="text-warning text-xs font-heading font-semibold tabular-nums">30.7%</strong>
                      <span className="text-[9px] text-text-muted block font-mono">2,146 acc</span>
                    </div>

                    <div className="p-1.5 rounded-md bg-surface border border-border">
                      <span className="text-[10px] text-text-muted block">High (p ≥ 0.70)</span>
                      <strong className="text-danger text-xs font-heading font-semibold tabular-nums">17.3%</strong>
                      <span className="text-[9px] text-text-muted block font-mono">1,210 acc</span>
                    </div>
                  </div>
                </div>

                {/* Regional Cohort Sample Strip */}
                <div className="p-3 rounded-lg bg-bg border border-border text-xs flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Compass className="w-4 h-4 text-electric shrink-0" />
                    <div>
                      <span className="font-heading font-semibold text-midnight text-xs block">Geographic Coverage</span>
                      <span className="text-[10px] text-text-muted">Multi-Region Dataset (15 States, 22 Major Hubs)</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 font-mono text-[10px] rounded bg-surface border border-border text-text-secondary">
                    Pan-India Sample
                  </span>
                </div>

                <div className="mt-4 pt-3 border-t border-border text-[10px] text-text-muted italic text-center">
                  * Model prediction distribution evaluated on 7,000 customer development dataset. Dec 31, 2025 observation cutoff. Not connected to external live databases.
                </div>
              </div>
            </div>

            {/* Right Column: Text & Strategic Analytics */}
            <div className="lg:col-span-6 order-1 lg:order-2 flex flex-col items-start">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-text-secondary text-xs font-mono font-medium mb-3">
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Feature 04 • Analytics Suite</span>
              </div>

              <h3 className="font-heading text-2xl sm:text-3xl font-semibold text-midnight tracking-tight mb-4">
                Actionable Cohort Analytics & Risk Visibility
              </h3>

              <p className="text-base text-text-secondary leading-relaxed mb-6">
                Understand macro-level customer health and drill down into cohort specifics. RetainIQ provides operational teams with clear visibility into churn distribution across Indian geographic hubs, order tiers, and behavioral personas.
              </p>

              <div className="space-y-3 w-full">
                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <BarChart3 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">Macro-to-Micro Exploration</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Move seamlessly from cohort-level churn prevalence down to individual customer behavioral diagnostics and friction histories.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <Sliders className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">Threshold-Aligned Risk Visibility</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      Filter customer cohorts by the official τ = 0.50 decision threshold, distinguishing safe repeaters from customers requiring immediate intervention.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-surface border border-border shadow-subtle">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-text-secondary flex items-center justify-center shrink-0 mt-0.5">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-heading text-sm font-semibold text-midnight">Verifiable Academic Metrics</h4>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">
                      All cohort summaries reflect empirical distributions from the project's 7,000 sanitized customer dataset without fabricated performance claims.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* CLOSING SECTION TRANSITION BANNER                        */}
        {/* ======================================================== */}
        <div className="rounded-xl bg-midnight p-8 sm:p-10 text-white shadow-card border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-xl">
            <span className="px-2.5 py-1 text-xs font-mono font-medium rounded bg-slate-800 text-slate-300 border border-slate-700 inline-block mb-3">
              TECHNICAL ARCHITECTURE • DUAL-CORE ML PIPELINE
            </span>
            <h3 className="font-heading text-xl sm:text-2xl font-semibold tracking-tight mb-2 text-white">
              Ready to Explore the Underlying Machine Learning Architecture?
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Discover how our 43-feature pipeline, Random Forest Configuration D, KMeans clustering, and FastAPI JWKS verification engine work together.
            </p>
          </div>

          <Button
            variant="primary"
            size="lg"
            icon={ArrowRight}
            iconPosition="right"
            onClick={handleTechArchitectureClick}
            className="shrink-0 text-sm font-semibold"
          >
            Preview Technical Architecture
          </Button>
        </div>
      </Container>
    </section>
  );
}
