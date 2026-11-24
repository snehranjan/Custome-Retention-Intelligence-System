/**
 * RetainIQ Customer Retention Intelligence System
 * Module 1: Overview Dashboard (Phase 8.4.8)
 */

import React, { useState, useEffect } from "react";
import {
  Users,
  AlertTriangle,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  MapPin,
  Layers,
  Database,
  Cpu,
  RefreshCw,
  Loader2,
  Calendar,
  Clock,
  ArrowUpRight,
} from "lucide-react";
import { apiClient } from "../../lib/apiClient";

export function OverviewDashboard({ onNavigateTab }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.analytics.getOverview();
      if (res?.success && res?.data) {
        setAnalytics(res.data);
      } else {
        setError("Failed to load overview analytics data.");
      }
    } catch (err) {
      setError(err.message || "Error loading overview data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-secondary">
        <Loader2 className="w-7 h-7 animate-spin text-electric mb-3" />
        <p className="text-xs font-mono text-text-muted">Aggregating cohort intelligence across 7,000 customers...</p>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-center space-y-3">
        <AlertTriangle className="w-7 h-7 text-rose-500 mx-auto" />
        <h3 className="font-heading font-semibold text-rose-900 text-sm">Analytics Service Unavailable</h3>
        <p className="text-xs text-rose-700 font-mono">{error}</p>
        <button
          onClick={fetchOverview}
          className="px-3.5 py-1.5 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const { kpis, observed_churn_distribution, predicted_risk_distribution, segment_distribution, state_distribution, dataset_metadata, model_metadata } = analytics;

  return (
    <div className="space-y-7 sm:space-y-8">
      {/* Header with Snapshot & Refresh */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div>
          <h2 className="font-heading text-lg font-semibold text-midnight">
            Executive Retention Intelligence Overview
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Cohort diagnostics across 7,000 synthetic Indian e-commerce customer accounts.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="text-[11px] font-mono px-3 py-1.5 rounded-lg bg-surface border border-border text-text-muted flex items-center gap-2 shadow-subtle">
            <Calendar className="w-3.5 h-3.5 text-electric" /> Snapshot: 31 Dec 2025
          </span>
          <button
            onClick={fetchOverview}
            className="p-2 rounded-lg border border-border bg-surface hover:bg-slate-50 text-text-secondary transition shadow-subtle"
            title="Refresh Analytics"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Master KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {/* Card 1: Customer Base */}
        <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-3">
          <div className="flex items-center justify-between text-xs text-text-muted font-medium">
            <span>Customer Population</span>
            <Users className="w-4 h-4 text-electric" />
          </div>
          <div className="font-heading font-semibold text-2xl text-midnight tabular-nums">
            {kpis.total_customers.toLocaleString()}
          </div>
          <div className="text-[11.5px] text-text-secondary flex items-center justify-between pt-1">
            <span>Observed Retained:</span>
            <span className="font-mono font-medium text-emerald-700 tabular-nums">
              {kpis.observed_retained.toLocaleString()} ({((kpis.observed_retained / kpis.total_customers) * 100).toFixed(1)}%)
            </span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mt-1.5">
            <div className="bg-emerald-600 h-full rounded-full" style={{ width: `${(kpis.observed_retained / kpis.total_customers) * 100}%` }} />
          </div>
        </div>

        {/* Card 2: Observed Churned */}
        <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-3">
          <div className="flex items-center justify-between text-xs text-text-muted font-medium">
            <span>Observed Ground Truth Churn</span>
            <TrendingDown className="w-4 h-4 text-rose-500" />
          </div>
          <div className="font-heading font-semibold text-2xl text-midnight flex items-baseline gap-2 tabular-nums">
            <span>{kpis.observed_churned.toLocaleString()}</span>
            <span className="text-xs font-mono font-medium text-rose-700">({(kpis.observed_churn_rate * 100).toFixed(2)}%)</span>
          </div>
          <p className="text-[11.5px] text-text-secondary leading-normal">
            Historical outcomes over the 90-day window (1 Jan – 31 Mar 2026).
          </p>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mt-1.5">
            <div className="bg-rose-500 h-full rounded-full" style={{ width: `${kpis.observed_churn_rate * 100}%` }} />
          </div>
        </div>

        {/* Card 3: Predicted At-Risk */}
        <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-3">
          <div className="flex items-center justify-between text-xs text-text-muted font-medium">
            <span>Model Predicted At-Risk</span>
            <Cpu className="w-4 h-4 text-amber-500" />
          </div>
          <div className="font-heading font-semibold text-2xl text-midnight flex items-baseline gap-2 tabular-nums">
            <span>{kpis.predicted_at_risk.toLocaleString()}</span>
            <span className="text-xs font-mono font-medium text-amber-700">({(kpis.predicted_at_risk_rate * 100).toFixed(2)}%)</span>
          </div>
          <p className="text-[11.5px] text-text-secondary leading-normal">
            Accounts with churn probability score <span className="font-mono font-medium text-midnight">p ≥ 0.50</span>.
          </p>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mt-1.5">
            <div className="bg-amber-500 h-full rounded-full" style={{ width: `${kpis.predicted_at_risk_rate * 100}%` }} />
          </div>
        </div>

        {/* Card 4: High Risk Priority */}
        <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-3">
          <div className="flex items-center justify-between text-xs text-text-muted font-medium">
            <span>Critical Interventions (p ≥ 0.70)</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="font-heading font-semibold text-2xl text-midnight flex items-baseline gap-2 tabular-nums">
            <span>1,210</span>
            <span className="text-xs font-mono font-medium text-rose-700">(17.29%)</span>
          </div>
          <p className="text-[11.5px] text-text-secondary leading-normal">
            High risk cohort requiring immediate prescriptive retention outreach.
          </p>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden mt-1.5">
            <div className="bg-rose-600 h-full rounded-full" style={{ width: "17.29%" }} />
          </div>
        </div>
      </div>

      {/* Grid Row 2: Churn Distributions & Risk Tiers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6">
        {/* Risk Tier Distribution */}
        <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-heading font-semibold text-sm text-midnight">
                Predicted Churn Risk Tiers
              </h3>
              <p className="text-xs text-text-secondary mt-1">
                Model probability distribution with locked decision boundary (τ = 0.50)
              </p>
            </div>
            <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-700 font-medium border border-slate-200">
              Config D
            </span>
          </div>

          {/* Horizontal multi-tier bar */}
          <div className="w-full h-2.5 rounded bg-slate-100 flex overflow-hidden">
            {predicted_risk_distribution.map((tier) => (
              <div
                key={tier.tier}
                style={{ width: `${tier.percentage}%`, backgroundColor: tier.color }}
                title={`${tier.label}: ${tier.count} (${tier.percentage}%)`}
              />
            ))}
          </div>

          {/* Tier Cards Breakdown */}
          <div className="grid grid-cols-3 gap-3.5">
            {predicted_risk_distribution.map((tier) => (
              <div key={tier.tier} className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs font-medium" style={{ color: tier.color }}>
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: tier.color }} />
                  <span>{tier.tier}</span>
                </div>
                <div className="font-heading font-semibold text-lg text-midnight tabular-nums">
                  {tier.count.toLocaleString()}
                </div>
                <div className="text-[11px] font-mono text-text-secondary flex justify-between tabular-nums pt-0.5">
                  <span>{tier.percentage}%</span>
                  <span className="text-text-muted">{tier.range}</span>
                </div>
              </div>
            ))}
          </div>

          <p className="text-[11px] text-text-muted leading-relaxed">
            * Threshold τ = 0.50 locked by Phase 5.1 evaluation. Scores below 0.50 classified as Retained; scores ≥ 0.50 classified as Churn.
          </p>
        </div>

        {/* Observed vs Predicted Calibration */}
        <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-heading font-semibold text-sm text-midnight">
                Observed vs. Predicted Distribution
              </h3>
              <p className="text-xs text-text-secondary mt-1">
                Comparison of actual ground truth outcomes against model classification
              </p>
            </div>
          </div>

          <div className="space-y-4 pt-1">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1.5">
                <span className="text-text-secondary">Observed Ground Truth (90-Day Window)</span>
                <span className="font-mono text-rose-700 font-medium tabular-nums">45.81% Churned (3,207)</span>
              </div>
              <div className="w-full h-2.5 rounded bg-slate-100 flex overflow-hidden">
                <div className="bg-rose-500 h-full" style={{ width: "45.81%" }} />
                <div className="bg-emerald-600 h-full" style={{ width: "54.19%" }} />
              </div>
              <div className="flex justify-between text-[11px] font-mono text-text-muted mt-1.5 tabular-nums">
                <span>3,207 Churned</span>
                <span>3,793 Retained (54.19%)</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1.5">
                <span className="text-text-secondary">Model Predicted (τ = 0.50)</span>
                <span className="font-mono text-amber-700 font-medium tabular-nums">47.94% At-Risk (3,356)</span>
              </div>
              <div className="w-full h-2.5 rounded bg-slate-100 flex overflow-hidden">
                <div className="bg-amber-500 h-full" style={{ width: "47.94%" }} />
                <div className="bg-emerald-600 h-full" style={{ width: "52.06%" }} />
              </div>
              <div className="flex justify-between text-[11px] font-mono text-text-muted mt-1.5 tabular-nums">
                <span>3,356 Predicted Churn</span>
                <span>3,644 Predicted Retained (52.06%)</span>
              </div>
            </div>
          </div>

          <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-text-secondary leading-relaxed">
            The Random Forest classifier exhibits a modest <strong>+2.13%</strong> positive classification bias, intentionally balancing sensitivity for proactive retention outreach without catastrophic false alarms.
          </div>
        </div>
      </div>

      {/* Grid Row 3: 5 Official Customer Personas Summary */}
      <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5">
          <div>
            <h3 className="font-heading font-semibold text-sm text-midnight">
              RFM Customer Persona Segments (K = 5)
            </h3>
            <p className="text-xs text-text-secondary mt-1">
              Authoritative segmentation mapping customer share, observed churn, and operational strategies
            </p>
          </div>
          <button
            onClick={() => onNavigateTab("segments")}
            className="text-xs font-medium text-electric hover:underline flex items-center gap-1.5"
          >
            <span>Deep Dive in Segmentation Explorer</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-slate-50/75 text-text-muted font-mono uppercase text-[10px]">
                <th className="py-3 px-4">Persona</th>
                <th className="py-3 px-4 text-right">Population</th>
                <th className="py-3 px-4 text-right">Share %</th>
                <th className="py-3 px-4 text-right">Observed Churn</th>
                <th className="py-3 px-4 text-right">Avg Spend (INR)</th>
                <th className="py-3 px-4">Primary Retention Strategy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {segment_distribution.map((s) => (
                <tr key={s.cluster_id} className="hover:bg-slate-50/60 transition">
                  <td className="py-3.5 px-4">
                    <div className="font-medium text-midnight">{s.segment_name}</div>
                    <div className="text-[10px] font-mono text-text-muted">Cluster {s.cluster_id}</div>
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-medium text-midnight tabular-nums">
                    {s.customer_count.toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-text-secondary tabular-nums">
                    {s.share_percentage}%
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-medium tabular-nums">
                    <span className={s.observed_churn_rate >= 50 ? "text-rose-700" : "text-emerald-700"}>
                      {s.observed_churn_rate}%
                    </span>
                    <span className="text-[10px] text-text-muted block font-normal">({s.observed_churn_count})</span>
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-text-secondary tabular-nums">
                    ₹{s.avg_monetary_inr.toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4 text-text-secondary text-[11px] max-w-xs leading-relaxed">
                    {s.recommended_strategy}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grid Row 4: Dataset & Model Provenance Disclosures */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5">
        {/* Dataset Provenance */}
        <div className="p-5 sm:p-6 rounded-xl bg-surface border border-border shadow-subtle space-y-3">
          <div className="flex items-center gap-2 text-xs font-heading font-semibold text-midnight uppercase tracking-wider">
            <Database className="w-4 h-4 text-electric" /> Dataset Provenance & Windowing
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            {dataset_metadata.provenance_disclosure}
          </p>
          <div className="grid grid-cols-2 gap-2.5 pt-1.5 font-mono text-[11px] text-text-muted">
            <div>Snapshot Date: <strong className="text-midnight">{dataset_metadata.observation_snapshot}</strong></div>
            <div>Outcome Window: <strong className="text-midnight">90 Days</strong></div>
            <div>Geographies: <strong className="text-midnight">{dataset_metadata.states_covered} States, {dataset_metadata.cities_covered} Cities</strong></div>
            <div>Total Orders: <strong className="text-midnight">{dataset_metadata.order_records.toLocaleString()}</strong></div>
          </div>
        </div>

        {/* Model Integrity */}
        <div className="p-5 sm:p-6 rounded-xl bg-surface border border-border shadow-subtle space-y-3">
          <div className="flex items-center gap-2 text-xs font-heading font-semibold text-midnight uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-emerald-700" /> Model Invariance & Cryptographic Integrity
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            The production pipeline is frozen and audited against accidental fine-tuning or threshold alteration.
          </p>
          <div className="space-y-1.5 pt-1.5 font-mono text-[11px] text-text-muted">
            <div>Model: <strong className="text-midnight">{model_metadata.model_name} (v{model_metadata.model_version})</strong></div>
            <div>Locked Threshold: <strong className="text-midnight">τ = {model_metadata.decision_threshold.toFixed(2)}</strong></div>
            <div className="truncate">SHA-256: <strong className="text-midnight text-[10px]">{model_metadata.model_sha256}</strong></div>
          </div>
        </div>
      </div>
    </div>
  );
}
