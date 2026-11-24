/**
 * RetainIQ Customer Retention Intelligence System
 * Module 3: Churn Prediction Explorer (Phase 8.4.8)
 */

import React, { useState, useEffect } from "react";
import {
  BrainCircuit,
  Search,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  TrendingDown,
  Layers,
  Cpu,
  RefreshCw,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { apiClient } from "../../lib/apiClient";

export function PredictionExplorer({ initialCustomerId = "IND_CUST_10001" }) {
  const [customerId, setCustomerId] = useState(initialCustomerId);
  const [loading, setLoading] = useState(false);
  const [predictionData, setPredictionData] = useState(null);
  const [customerProfile, setCustomerProfile] = useState(null);
  const [error, setError] = useState(null);

  // Quick sample IDs
  const sampleCustomers = [
    { id: "IND_CUST_10001", label: "IND_CUST_10001 (High Risk Sample)" },
    { id: "IND_CUST_10002", label: "IND_CUST_10002 (Low Risk Sample)" },
    { id: "IND_CUST_10004", label: "IND_CUST_10004 (Moderate Risk Sample)" },
    { id: "IND_CUST_10010", label: "IND_CUST_10010 (Champion Sample)" },
  ];

  const runPrediction = async (idToPredict) => {
    const targetId = (idToPredict || customerId).trim();
    if (!targetId) return;

    setLoading(true);
    setError(null);

    try {
      // Parallel fetch: get full customer profile (features & metadata) + execute live prediction
      const [profileRes, predictRes] = await Promise.all([
        apiClient.customers.getById(targetId),
        apiClient.customers.predict(targetId),
      ]);

      if (profileRes?.success && profileRes?.data) {
        setCustomerProfile(profileRes.data);
      }
      if (predictRes?.success && predictRes?.data) {
        setPredictionData(predictRes.data);
      }
    } catch (err) {
      setError(err.message || "Failed to execute prediction inference.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runPrediction(initialCustomerId);
  }, []);

  const prob = predictionData ? predictionData.churn_probability : 0;
  const probPercent = (prob * 100).toFixed(1);
  const isChurn = predictionData ? predictionData.predicted_class === 1 : false;
  const riskTier = predictionData ? predictionData.risk_tier : "LOW";

  return (
    <div className="space-y-7 sm:space-y-8">
      {/* Search & Selector Header */}
      <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-4 sm:space-y-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div>
            <h2 className="font-heading text-lg font-semibold text-midnight flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-electric" />
              Real-Time Churn Prediction Engine
            </h2>
            <p className="text-xs text-text-secondary mt-1">
              Direct inference on the locked Random Forest Config D pipeline with decision threshold τ = 0.50.
            </p>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 shadow-subtle">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>SHA-256 Verified Pipeline</span>
          </div>
        </div>

        {/* Input Bar & Samples */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-text-muted absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Enter Customer ID (e.g. IND_CUST_10001)..."
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runPrediction()}
              className="w-full pl-9 pr-3.5 py-2.5 text-xs bg-bg border border-border rounded-lg focus:outline-none focus:border-electric focus:ring-1 focus:ring-electric/20 font-mono text-midnight placeholder:text-text-muted"
            />
          </div>
          <button
            disabled={loading}
            onClick={() => runPrediction()}
            className="px-5 py-2.5 text-xs font-medium rounded-lg bg-electric text-white hover:bg-electric-hover disabled:opacity-50 transition flex items-center justify-center gap-2 shadow-subtle"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Cpu className="w-3.5 h-3.5" />}
            <span>Evaluate Churn Risk</span>
          </button>
        </div>

        {/* Sample Customer Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-0.5 text-xs text-text-secondary">
          <span className="text-[11px] font-mono text-text-muted">Quick Inspect:</span>
          {sampleCustomers.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                setCustomerId(s.id);
                runPrediction(s.id);
              }}
              className="px-3 py-1 rounded-md bg-slate-50 border border-slate-200 hover:border-slate-300 text-[11px] font-mono text-midnight transition shadow-subtle"
            >
              {s.id}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-mono flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {predictionData && customerProfile && (
        <div className="space-y-7 sm:space-y-8">
          {/* Main Inference Diagnostic Card */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6">
            {/* Left 2 Cols: Probability Gauge & Decision Boundary */}
            <div className="lg:col-span-2 p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-medium border border-slate-200">
                    Inference Output
                  </span>
                  <h3 className="font-heading font-semibold text-lg text-midnight mt-1.5">
                    {customerProfile.customer_name} ({customerProfile.customer_id})
                  </h3>
                  <p className="text-xs text-text-secondary mt-1">
                    {customerProfile.city}, {customerProfile.state} • {customerProfile.current_segment?.segment_name}
                  </p>
                </div>
                <div className="text-left sm:text-right">
                  <span className={`inline-block px-3 py-1 rounded-lg text-xs font-mono font-medium border ${
                    riskTier === "HIGH"
                      ? "text-rose-700 bg-rose-50 border-rose-200"
                      : riskTier === "MODERATE"
                      ? "text-amber-700 bg-amber-50 border-amber-200"
                      : "text-emerald-700 bg-emerald-50 border-emerald-200"
                  }`}>
                    {riskTier} RISK TIER
                  </span>
                </div>
              </div>

              {/* Big Score Display */}
              <div className="p-5 sm:p-6 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                  <div className="text-xs font-mono text-text-muted uppercase">Model Churn Probability</div>
                  <div className="font-heading font-semibold text-4xl text-midnight mt-1.5 tabular-nums">
                    {probPercent}%
                  </div>
                  <div className="text-xs font-mono text-text-secondary mt-1.5 tabular-nums">
                    Retention Probability: <strong className="text-emerald-700">{(predictionData.retention_probability * 100).toFixed(1)}%</strong>
                  </div>
                </div>

                {/* Classification Decision Badge */}
                <div className="p-4 sm:p-4.5 rounded-xl bg-surface border border-slate-200 text-center w-full sm:w-auto sm:min-w-[200px] space-y-1.5 shadow-subtle">
                  <div className="text-[10px] font-mono text-text-muted uppercase">Predicted Class</div>
                  <div className={`font-heading font-semibold text-base ${isChurn ? "text-rose-700" : "text-emerald-700"}`}>
                    {isChurn ? "CHURN RISK (1)" : "RETAINED (0)"}
                  </div>
                  <div className="text-[10px] font-mono text-text-muted">
                    Decision Threshold: <strong>τ = 0.50</strong>
                  </div>
                </div>
              </div>

              {/* Decision Threshold Spectrum Bar */}
              <div className="space-y-2.5 pt-1">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-emerald-700 font-medium">0.0 (Retained)</span>
                  <span className="text-midnight font-medium flex items-center gap-1">
                    <span>Locked Cutoff: τ = 0.50</span>
                  </span>
                  <span className="text-rose-700 font-medium">1.0 (Churn)</span>
                </div>

                <div className="relative w-full h-2.5 bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500 rounded-full overflow-hidden">
                  {/* Cutoff Marker Line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-midnight z-10"
                    style={{ left: "50%" }}
                    title="Decision Threshold τ = 0.50"
                  />
                </div>

                {/* Pointer for Current Customer */}
                <div className="relative w-full h-5">
                  <div
                    className="absolute -top-1 -translate-x-1/2 flex flex-col items-center transition-all duration-300"
                    style={{ left: `${Math.min(98, Math.max(2, prob * 100))}%` }}
                  >
                    <div className="w-2.5 h-2.5 bg-midnight rotate-45" />
                    <span className="text-[10px] font-mono font-medium text-midnight whitespace-nowrap mt-0.5 tabular-nums">
                      {probPercent}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right 1 Col: Evaluation Invariants & Provenance */}
            <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-4 sm:space-y-5">
              <h4 className="font-heading font-semibold text-xs text-midnight uppercase tracking-wider flex items-center gap-2">
                <Cpu className="w-4 h-4 text-electric" /> Model Specifications
              </h4>

              <div className="space-y-3 text-xs font-mono">
                <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                  <span className="text-text-muted block text-[10px]">ARCHITECTURE</span>
                  <span className="font-medium text-midnight">RandomForestClassifier</span>
                  <span className="text-[11px] text-text-secondary block">Config D (43 Features)</span>
                </div>

                <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                  <span className="text-text-muted block text-[10px]">DECISION BOUNDARY</span>
                  <span className="font-medium text-midnight">τ = 0.50 (Locked)</span>
                  <span className="text-[11px] text-text-secondary block">Empirical uncalibrated voting</span>
                </div>

                <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                  <span className="text-text-muted block text-[10px]">MODEL AUDIT CHECKSUM</span>
                  <span className="text-[10px] text-midnight font-medium break-all">
                    24F1F0E3...3438F301
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 43 Behavioral Features Breakdown Table */}
          <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-4 sm:space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-heading font-semibold text-sm text-midnight flex items-center gap-2">
                  <Layers className="w-4 h-4 text-electric" />
                  Authoritative 43 Behavioral Features Input Vector
                </h3>
                <p className="text-xs text-text-secondary mt-1">
                  Complete feature vector evaluated by Random Forest pipeline for {customerProfile.customer_id}.
                </p>
              </div>
              <span className="text-xs font-mono font-medium text-text-muted">
                40 Numerical + 3 Categorical
              </span>
            </div>

            {customerProfile.features ? (
              <div className="max-h-96 overflow-y-auto border border-border rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-slate-50 text-text-muted font-mono uppercase text-[10px] border-b border-border">
                    <tr>
                      <th className="py-2.5 px-4.5">#</th>
                      <th className="py-2.5 px-4.5">Feature Identifier</th>
                      <th className="py-2.5 px-4.5">Category</th>
                      <th className="py-2.5 px-4.5 text-right">Raw Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border font-mono text-[11.5px]">
                    {Object.entries(customerProfile.features).map(([key, val], idx) => {
                      let category = "Numerical Behavioral";
                      if (["city", "state", "cluster_id"].includes(key)) category = "Categorical / Segmentation";
                      else if (key.includes("velocity") || key.includes("friction")) category = "Engineered Momentum";
                      else if (key.includes("discount") || key.includes("cod") || key.includes("upi")) category = "Payment & Pricing";
                      else if (key.includes("delay")) category = "Fulfillment Friction";

                      return (
                        <tr key={key} className="hover:bg-slate-50/50 transition">
                          <td className="py-2.5 px-4.5 text-text-muted tabular-nums">{idx + 1}</td>
                          <td className="py-2.5 px-4.5 font-medium text-midnight">{key}</td>
                          <td className="py-2.5 px-4.5 text-text-secondary text-[11px]">{category}</td>
                          <td className="py-2.5 px-4.5 text-right font-medium text-midnight tabular-nums">
                            {val === null ? <span className="text-text-muted font-normal">null</span> : String(val)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-xs font-mono text-text-muted p-4">Loading features...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
