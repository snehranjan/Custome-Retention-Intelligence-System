/**
 * RetainIQ Customer Retention Intelligence System
 * Module 4: Customer Segmentation Explorer (Phase 8.4.8)
 */

import React, { useState, useEffect } from "react";
import {
  PieChart,
  Users,
  TrendingDown,
  DollarSign,
  Clock,
  Layers,
  ShieldCheck,
  ChevronRight,
  ArrowUpRight,
  RefreshCw,
  Loader2,
  AlertTriangle,
  Award,
  AlertCircle,
  HelpCircle,
  Repeat,
  Sparkles,
} from "lucide-react";
import { apiClient } from "../../lib/apiClient";

export function SegmentationExplorer({ onFilterSegmentInCustomerExplorer }) {
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCluster, setSelectedCluster] = useState(0);

  const fetchSegments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.analytics.getSegments();
      if (res?.success && res?.data) {
        setSegments(res.data);
      } else {
        setError("Failed to load segment profiles.");
      }
    } catch (err) {
      setError(err.message || "Error contacting segmentation API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSegments();
  }, []);

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-text-secondary">
        <Loader2 className="w-8 h-8 animate-spin text-electric mb-3" />
        <p className="text-xs font-mono">Loading 5 official RFM customer personas...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-center space-y-3">
        <AlertTriangle className="w-7 h-7 text-rose-500 mx-auto" />
        <h3 className="font-heading font-semibold text-rose-900 text-sm">Segmentation Service Error</h3>
        <p className="text-xs text-rose-700 font-mono">{error}</p>
        <button
          onClick={fetchSegments}
          className="px-3.5 py-1.5 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  const activeSegment = segments.find((s) => s.cluster_id === selectedCluster) || segments[0];

  const getPersonaIcon = (clusterId) => {
    switch (clusterId) {
      case 0:
        return <Award className="w-4.5 h-4.5 text-amber-500" />;
      case 1:
        return <AlertTriangle className="w-4.5 h-4.5 text-rose-500" />;
      case 2:
        return <AlertCircle className="w-4.5 h-4.5 text-rose-600" />;
      case 3:
        return <Repeat className="w-4.5 h-4.5 text-electric" />;
      case 4:
        return <Sparkles className="w-4.5 h-4.5 text-cyan" />;
      default:
        return <Users className="w-4.5 h-4.5 text-text-muted" />;
    }
  };

  return (
    <div className="space-y-7 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div>
          <h2 className="font-heading text-lg font-semibold text-midnight flex items-center gap-2">
            <PieChart className="w-5 h-5 text-electric" />
            Customer Segmentation & Persona Intelligence
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Pre-fitted K-Means RFM clustering (K=5) partitioning the 7,000 customer base into distinct operational tiers.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-text-muted bg-surface px-3.5 py-1.5 rounded-lg border border-border shadow-subtle">
          <Layers className="w-4 h-4 text-electric" />
          <span>K = 5 Personas</span>
        </div>
      </div>

      {/* Cluster Navigation Cards (5 Columns) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 sm:gap-4">
        {segments.map((s) => {
          const isSelected = s.cluster_id === selectedCluster;
          return (
            <div
              key={s.cluster_id}
              onClick={() => setSelectedCluster(s.cluster_id)}
              className={`p-4 sm:p-4.5 rounded-xl border transition cursor-pointer space-y-2.5 ${
                isSelected
                  ? "bg-surface border-electric shadow-subtle ring-1 ring-electric/30"
                  : "bg-surface border-border hover:border-slate-300 shadow-subtle"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                  {getPersonaIcon(s.cluster_id)}
                </div>
                <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-medium border border-slate-200">
                  Cluster {s.cluster_id}
                </span>
              </div>
              <div>
                <h3 className="font-heading font-medium text-xs text-midnight leading-tight line-clamp-1">
                  {s.segment_name}
                </h3>
                <div className="font-heading font-semibold text-lg text-midnight mt-1 tabular-nums">
                  {s.customer_count.toLocaleString()}
                </div>
                <div className="text-[11px] font-mono text-text-muted flex justify-between tabular-nums pt-0.5">
                  <span>{s.share_percentage}% share</span>
                  <span className={s.observed_churn_rate >= 50 ? "text-rose-700 font-medium" : "text-emerald-700 font-medium"}>
                    {s.observed_churn_rate}% churn
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Deep-Dive Card for Active Segment */}
      {activeSegment && (
        <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-border">
            <div className="flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-slate-50 text-electric border border-slate-200">
                {getPersonaIcon(activeSegment.cluster_id)}
              </div>
              <div>
                <div className="text-[10px] font-mono text-electric font-medium uppercase tracking-wider">
                  Persona Profile • Cluster {activeSegment.cluster_id}
                </div>
                <h3 className="font-heading font-semibold text-lg text-midnight mt-0.5">
                  {activeSegment.segment_name}
                </h3>
                <p className="text-xs text-text-secondary mt-1">
                  {activeSegment.persona_description}
                </p>
              </div>
            </div>

            <button
              onClick={() => onFilterSegmentInCustomerExplorer(activeSegment.cluster_id)}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-midnight text-white hover:bg-slate-800 transition flex items-center gap-2 shrink-0 shadow-subtle"
            >
              <span>Inspect {activeSegment.customer_count.toLocaleString()} Customers</span>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-300" />
            </button>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 sm:p-4.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <span className="text-[10px] font-mono text-text-muted uppercase">Customer Population</span>
              <div className="font-heading font-semibold text-xl text-midnight tabular-nums">
                {activeSegment.customer_count.toLocaleString()}
              </div>
              <div className="text-[11px] font-mono text-text-secondary tabular-nums">
                {activeSegment.share_percentage}% of total base
              </div>
            </div>

            <div className="p-4 sm:p-4.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <span className="text-[10px] font-mono text-text-muted uppercase">Observed Churn Rate</span>
              <div className={`font-heading font-semibold text-xl tabular-nums ${
                activeSegment.observed_churn_rate >= 50 ? "text-rose-700" : "text-emerald-700"
              }`}>
                {activeSegment.observed_churn_rate}%
              </div>
              <div className="text-[11px] font-mono text-text-secondary tabular-nums">
                {activeSegment.observed_churn_count.toLocaleString()} customers lost
              </div>
            </div>

            <div className="p-4 sm:p-4.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <span className="text-[10px] font-mono text-text-muted uppercase">Average Spend (INR)</span>
              <div className="font-heading font-semibold text-xl text-midnight font-mono tabular-nums">
                ₹{activeSegment.avg_monetary_inr.toLocaleString()}
              </div>
              <div className="text-[11px] font-mono text-text-secondary tabular-nums">
                {activeSegment.avg_delivered_orders} avg fulfilled orders
              </div>
            </div>

            <div className="p-4 sm:p-4.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <span className="text-[10px] font-mono text-text-muted uppercase">Cadence & Recency</span>
              <div className="font-heading font-semibold text-xl text-midnight font-mono tabular-nums">
                {Math.round(activeSegment.avg_recency_days)} days
              </div>
              <div className="text-[11px] font-mono text-text-secondary">
                avg since last order
              </div>
            </div>
          </div>

          {/* Recommended Operational Strategy */}
          <div className="p-4.5 sm:p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="text-xs font-heading font-semibold text-midnight uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-700" /> Recommended Prescriptive Retention Strategy
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              {activeSegment.recommended_strategy}
            </p>
          </div>
        </div>
      )}

      {/* Comparison Across All 5 Personas */}
      <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-4 sm:space-y-5">
        <h3 className="font-heading font-semibold text-sm text-midnight">
          Cross-Persona Churn Risk & Spend Diagnostic
        </h3>

        <div className="space-y-4 pt-1">
          {segments.map((s) => (
            <div key={s.cluster_id} className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="font-medium text-midnight">
                  Cluster {s.cluster_id}: {s.segment_name}
                </span>
                <span className="text-text-secondary tabular-nums">
                  Churn Rate: <strong className={s.observed_churn_rate >= 50 ? "text-rose-700" : "text-emerald-700"}>{s.observed_churn_rate}%</strong> • Avg Spend: <strong>₹{s.avg_monetary_inr.toLocaleString()}</strong>
                </span>
              </div>
              <div className="w-full h-2.5 rounded bg-slate-100 flex overflow-hidden">
                <div
                  className={s.observed_churn_rate >= 50 ? "bg-rose-500 h-full" : "bg-emerald-600 h-full"}
                  style={{ width: `${s.observed_churn_rate}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
