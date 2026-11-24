import React from "react";
import { motion } from "framer-motion";
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
  PieChart,
  Tag,
  Send,
  Sliders,
} from "lucide-react";
import { Container } from "../components/ui/Container";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";

/**
 * RetainIQ Platform Highlights & Value Proposition Section
 * Directly follows the Hero section with anchor id="platform".
 * Features four balanced capability cards communicating:
 * 1. AI-Powered Churn Prediction
 * 2. Intelligent Customer Segmentation (5 official segments)
 * 3. Retention Recommendations
 * 4. Actionable Customer Analytics
 */
export function PlatformHighlights({ onOpenActionModal }) {
  // Official project customer segments
  const officialSegments = [
    {
      id: 0,
      name: "Champions & High-Value Loyalists",
      color: "bg-purple-50 text-purple-700 border-purple-200",
      dot: "bg-purple-500",
      badge: "Cluster 0",
    },
    {
      id: 1,
      name: "At-Risk / Lapsed Low-Value Customers",
      color: "bg-amber-50 text-amber-700 border-amber-200",
      dot: "bg-amber-500",
      badge: "Cluster 1",
    },
    {
      id: 2,
      name: "Zero Delivered-Purchase Customers",
      color: "bg-rose-50 text-rose-700 border-rose-200",
      dot: "bg-rose-500",
      badge: "Cluster 2",
    },
    {
      id: 3,
      name: "Steady Core Repeaters",
      color: "bg-blue-50 text-blue-700 border-blue-200",
      dot: "bg-blue-500",
      badge: "Cluster 3",
    },
    {
      id: 4,
      name: "Recent Low-Ticket / New Promising Customers",
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
      dot: "bg-emerald-500",
      badge: "Cluster 4",
    },
  ];

  return (
    <section
      id="platform"
      className="relative py-14 sm:py-20 lg:py-24 bg-surface border-t border-border/80 scroll-mt-20"
    >
      <Container size="default" className="relative z-10">
        {/* Section Introduction */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-12 sm:mb-16">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface-muted border border-border text-xs font-mono text-text-secondary mb-3 shadow-subtle">
            <span className="w-1.5 h-1.5 rounded-full bg-electric" />
            <span>Platform Capabilities</span>
          </div>

          {/* Main Heading */}
          <h2 className="font-heading text-2xl sm:text-3xl md:text-4xl font-semibold text-midnight tracking-tight leading-tight mb-3">
            Core Retention Intelligence Infrastructure
          </h2>

          {/* Supporting Subheading */}
          <p className="text-sm sm:text-base text-text-secondary leading-relaxed font-normal max-w-2xl">
            From raw transaction telemetry to data-driven decision support: RetainIQ combines predictive inference, customer segmentation, and prescriptive playbooks.
          </p>
        </div>

        {/* 2 x 2 Feature Capability Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 lg:gap-6">
          {/* ======================================================== */}
          {/* CARD 1 — CHURN PREDICTION ENGINE                          */}
          {/* ======================================================== */}
          <div className="flex flex-col rounded-xl bg-surface border border-border p-5 sm:p-6 shadow-card hover:border-border-dark transition-colors duration-150">
            {/* Card Header & Icon */}
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-surface-muted border border-border flex items-center justify-center text-text-secondary shrink-0">
                <BrainCircuit className="w-4 h-4 text-electric" strokeWidth={1.75} />
              </div>
              <span className="px-2 py-0.5 text-[10.5px] font-mono text-text-secondary rounded border border-border bg-bg">
                Supervised Inference
              </span>
            </div>

            {/* Title & Description */}
            <h3 className="font-heading text-lg sm:text-xl font-semibold text-midnight tracking-tight mb-2">
              Supervised Churn Risk Modeling
            </h3>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed mb-5 font-normal">
              Detect customer defection risk before order dormancy becomes permanent. Evaluates 43 behavioral features using a locked Random Forest classifier with fixed decision threshold τ = 0.50.
            </p>

            {/* Visual Representation: Illustrative Risk Indicator */}
            <div className="mt-auto rounded-lg bg-bg border border-border/80 p-3.5 sm:p-4">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-[11px] font-mono text-midnight">
                  Risk Tier Partitioning
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                  Decision Cutoff: τ = 0.50
                </span>
              </div>

              {/* 3 Semantic Risk Tiers (Aligned with backend churn_service.py) */}
              <div className="grid grid-cols-3 gap-2 mb-2">
                <div className="p-2 rounded bg-surface border border-border/80 flex flex-col justify-between">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                    <span className="text-[11px] font-medium text-text-primary">
                      Low Risk
                    </span>
                  </div>
                  <div className="font-mono text-xs font-semibold text-emerald-800 tabular-nums">
                    p &lt; 0.50
                  </div>
                  <div className="text-[10px] font-mono text-text-muted mt-0.5">
                    Class 0 (Retained)
                  </div>
                </div>

                <div className="p-2 rounded bg-surface border border-border/80 flex flex-col justify-between">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                    <span className="text-[11px] font-medium text-text-primary">
                      Moderate Risk
                    </span>
                  </div>
                  <div className="font-mono text-xs font-semibold text-amber-800 tabular-nums">
                    0.50 ≤ p &lt; 0.70
                  </div>
                  <div className="text-[10px] font-mono text-text-muted mt-0.5">
                    Class 1 (At-Risk)
                  </div>
                </div>

                <div className="p-2 rounded bg-surface border border-border/80 flex flex-col justify-between">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0" />
                    <span className="text-[11px] font-medium text-text-primary">
                      High Risk
                    </span>
                  </div>
                  <div className="font-mono text-xs font-semibold text-rose-800 tabular-nums">
                    p ≥ 0.70
                  </div>
                  <div className="text-[10px] text-text-muted mt-0.5">
                    Class 1 (Severe)
                  </div>
                </div>
              </div>

              {/* Separate Binary Model Decision Threshold */}
              <div className="pt-2.5 border-t border-border/60 space-y-1">
                <div className="text-[10.5px] text-text-secondary flex items-center justify-between">
                  <span>Model Decision Threshold</span>
                  <span className="font-heading font-bold text-midnight">τ = 0.50</span>
                </div>
                <div className="text-[9.5px] text-text-muted italic leading-snug">
                  * Illustrative sample prediction preview aligned with backend risk-tier classification logic.
                </div>
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* CARD 2 — INTELLIGENT CUSTOMER SEGMENTATION                */}
          {/* ======================================================== */}
          <div className="flex flex-col rounded-xl bg-surface border border-border p-5 sm:p-6 shadow-card hover:border-border-dark transition-colors duration-150">
            {/* Card Header & Icon */}
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-surface-muted border border-border flex items-center justify-center text-text-secondary shrink-0">
                <Users className="w-4 h-4 text-cyan-dark" strokeWidth={1.75} />
              </div>
              <span className="px-2 py-0.5 text-[10.5px] font-mono text-text-secondary rounded border border-border bg-bg">
                KMeans (K=5)
              </span>
            </div>

            {/* Title & Description */}
            <h3 className="font-heading text-lg sm:text-xl font-semibold text-midnight tracking-tight mb-2">
              Behavioral RFM Segmentation
            </h3>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed mb-5 font-normal">
              Partition customer accounts into 5 distinct behavioural archetypes using normalized Recency, Frequency, and Monetary vectors with stable multi-seed cluster convergence.
            </p>

            {/* Visual Representation: 5 Official Project Segments */}
            <div className="mt-auto rounded-lg bg-bg border border-border/80 p-3.5 sm:p-4">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-[11px] font-mono text-midnight">
                  Official Personas (K=5)
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                  Centroid Mapping
                </span>
              </div>

              {/* List of 5 Official Persona Badges */}
              <div className="space-y-1">
                {officialSegments.map((segment) => (
                  <div
                    key={segment.id}
                    className="flex items-center justify-between p-1.5 px-2 rounded bg-surface border border-border/60 hover:border-border transition-colors gap-2 text-xs"
                  >
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className={`w-1.5 h-1.5 rounded-full ${segment.dot} shrink-0`} />
                      <span
                        className="font-medium text-text-primary text-[11px] truncate"
                        title={segment.name}
                      >
                        {segment.name}
                      </span>
                    </div>
                    <span className="shrink-0 px-1.5 py-0.2 text-[10px] font-mono text-text-secondary rounded bg-surface-muted border border-border">
                      {segment.badge}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* CARD 3 — RETENTION RECOMMENDATIONS                        */}
          {/* ======================================================== */}
          <div className="flex flex-col rounded-xl bg-surface border border-border p-5 sm:p-6 shadow-card hover:border-border-dark transition-colors duration-150">
            {/* Card Header & Icon */}
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-surface-muted border border-border flex items-center justify-center text-text-secondary shrink-0">
                <Lightbulb className="w-4 h-4 text-amber-600" strokeWidth={1.75} />
              </div>
              <span className="px-2 py-0.5 text-[10.5px] font-mono text-text-secondary rounded border border-border bg-bg">
                Rule Engine
              </span>
            </div>

            {/* Title & Description */}
            <h3 className="font-heading text-lg sm:text-xl font-semibold text-midnight tracking-tight mb-2">
              Prescriptive Retention Playbooks
            </h3>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed mb-5 font-normal">
              Execute explainable, rule-based interventions linked directly to diagnostic friction signals like delivery SLA delays, discount dependency, or recency drift.
            </p>

            {/* Visual Representation: Compact Recommendation Preview */}
            <div className="mt-auto rounded-lg bg-bg border border-border/80 p-3.5 sm:p-4">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-[11px] font-mono text-midnight">
                  Prescribed Action
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                  Illustrative Strategy
                </span>
              </div>

              {/* Recommendation Content Card */}
              <div className="p-3 rounded bg-surface border border-border/70 shadow-subtle space-y-2">
                {/* Risk Category Row */}
                <div className="flex items-center justify-between text-xs pb-1.5 border-b border-border/60">
                  <span className="text-text-muted text-[11px]">Target Cohort</span>
                  <Badge variant="high_risk" dot={true} size="sm">
                    High Risk (p ≥ 0.70)
                  </Badge>
                </div>

                {/* Example Retention Action */}
                <div>
                  <div className="text-[10px] font-mono font-medium text-text-secondary uppercase tracking-wide mb-0.5">
                    Recommended Action
                  </div>
                  <div className="text-xs text-text-primary leading-snug">
                    Proactive ₹150 delivery credit and dispatch priority upgrade to Express SLA.
                  </div>
                </div>

                {/* Engagement Channel */}
                <div className="flex items-center justify-between text-xs pt-1.5 border-t border-border/60">
                  <span className="text-text-muted text-[11px]">Primary Channel</span>
                  <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-muted text-text-secondary text-[11px] font-mono border border-border">
                    <Send className="w-3 h-3 text-electric" />
                    <span>Email & WhatsApp Alert</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* CARD 4 — ACTIONABLE CUSTOMER ANALYTICS                    */}
          {/* ======================================================== */}
          <div className="flex flex-col rounded-xl bg-surface border border-border p-5 sm:p-6 shadow-card hover:border-border-dark transition-colors duration-150">
            {/* Card Header & Icon */}
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-surface-muted border border-border flex items-center justify-center text-text-secondary shrink-0">
                <BarChart3 className="w-4 h-4 text-emerald-600" strokeWidth={1.75} />
              </div>
              <span className="px-2 py-0.5 text-[10.5px] font-mono text-text-secondary rounded border border-border bg-bg">
                Cohort Analytics
              </span>
            </div>

            {/* Title & Description */}
            <h3 className="font-heading text-lg sm:text-xl font-semibold text-midnight tracking-tight mb-2">
              Actionable Customer Analytics
            </h3>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed mb-5 font-normal">
              Inspect macro cohort health metrics, confusion matrix evaluations, and individual customer diagnostics through an integrated operational console.
            </p>

            {/* Visual Representation: Compact Analytical Summary */}
            <div className="mt-auto rounded-lg bg-bg border border-border/80 p-3.5 sm:p-4">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-[11px] font-mono text-midnight">
                  Cohort Summary
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-muted">
                  N = 7,000 Accounts
                </span>
              </div>

              {/* Segmented Distribution Bar (6px radius) */}
              <div className="h-2 w-full rounded-md bg-surface-muted flex overflow-hidden p-0.5 gap-0.5 mb-2.5 border border-border/60">
                <div className="h-full rounded-xs bg-emerald-500" style={{ width: "54.2%" }} title="Low Risk: 54.2%" />
                <div className="h-full rounded-xs bg-amber-500" style={{ width: "19.5%" }} title="Moderate: 19.5%" />
                <div className="h-full rounded-xs bg-rose-500" style={{ width: "26.3%" }} title="High Risk: 26.3%" />
              </div>

              {/* Analytical Summary Grid */}
              <div className="grid grid-cols-3 gap-1.5 pt-1.5 border-t border-border/60 text-center">
                <div className="p-1.5 rounded bg-surface border border-border/70">
                  <div className="text-[10px] text-text-muted font-mono">Cohort Total</div>
                  <div className="font-mono font-semibold text-xs text-midnight mt-0.5 tabular-nums">7,000</div>
                  <div className="text-[9px] text-text-secondary font-mono">Dec 31 Cutoff</div>
                </div>

                <div className="p-1.5 rounded bg-surface border border-border/70">
                  <div className="text-[10px] text-text-muted font-mono">Personas</div>
                  <div className="font-mono font-semibold text-xs text-midnight mt-0.5">5 Clusters</div>
                  <div className="text-[9px] text-text-secondary font-mono">KMeans Centroids</div>
                </div>

                <div className="p-1.5 rounded bg-surface border border-border/70">
                  <div className="text-[10px] text-text-muted font-mono">At-Risk Rate</div>
                  <div className="font-mono font-semibold text-xs text-rose-800 mt-0.5 tabular-nums">26.3%</div>
                  <div className="text-[9px] text-text-secondary font-mono">p ≥ 0.50 cutoff</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
