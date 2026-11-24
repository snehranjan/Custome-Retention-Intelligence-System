/**
 * RetainIQ Customer Retention Intelligence System
 * Module 6: Analytics & Model Performance (Phase 8.4.8)
 */

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  ShieldCheck,
  Cpu,
  Layers,
  Database,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Info,
} from "lucide-react";
import { apiClient } from "../../lib/apiClient";

export function AnalyticsPerformance() {
  const [perfData, setPerfData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPerformance = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.analytics.getModelPerformance();
      if (res?.success && res?.data) {
        setPerfData(res.data);
      } else {
        setError("Failed to fetch model performance metrics.");
      }
    } catch (err) {
      setError(err.message || "Error contacting analytics endpoint.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, []);

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-text-secondary">
        <Loader2 className="w-8 h-8 animate-spin text-electric mb-3" />
        <p className="text-xs font-mono">Loading model performance metrics and evaluation matrix...</p>
      </div>
    );
  }

  if (error || !perfData) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-center space-y-3">
        <AlertTriangle className="w-7 h-7 text-rose-500 mx-auto" />
        <h3 className="font-heading font-semibold text-rose-900 text-sm">Performance Report Unavailable</h3>
        <p className="text-xs text-rose-700 font-mono">{error}</p>
        <button
          onClick={fetchPerformance}
          className="px-3.5 py-1.5 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  const { metrics, confusion_matrix, class_distributions, hyperparameters } = perfData;

  return (
    <div className="space-y-7 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div>
          <h2 className="font-heading text-lg font-semibold text-midnight flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-electric" />
            Independent Model Performance & Evaluation Scorecard
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Rigorous evaluation on held-out independent synthetic test cohort (N = 1,500) with locked decision boundary τ = 0.50.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="text-[11px] font-mono px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-2 shadow-subtle">
            <ShieldCheck className="w-3.5 h-3.5" /> Frozen Production Checkpoint
          </span>
          <button
            onClick={fetchPerformance}
            className="p-2 rounded-lg border border-border bg-surface hover:bg-slate-50 text-text-secondary transition shadow-subtle"
            title="Refresh Metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Primary Metrics Scorecard */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5 sm:gap-4">
        {/* Accuracy */}
        <div className="p-4 sm:p-4.5 bg-surface border border-border rounded-xl shadow-subtle space-y-1.5">
          <span className="text-[10px] font-mono text-text-muted uppercase">Accuracy</span>
          <div className="font-heading font-semibold text-2xl text-midnight font-mono tabular-nums">
            {(metrics.accuracy * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-text-secondary tabular-nums">Balanced: {(metrics.balanced_accuracy * 100).toFixed(2)}%</span>
        </div>

        {/* Recall */}
        <div className="p-4 sm:p-4.5 bg-surface border border-border rounded-xl shadow-subtle space-y-1.5">
          <span className="text-[10px] font-mono text-text-muted uppercase">Recall (Sensitivity)</span>
          <div className="font-heading font-semibold text-2xl text-electric font-mono tabular-nums">
            {(metrics.recall * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-text-secondary tabular-nums">
            {confusion_matrix.true_positives} / {confusion_matrix.true_positives + confusion_matrix.false_negatives} churners
          </span>
        </div>

        {/* Precision */}
        <div className="p-4 sm:p-4.5 bg-surface border border-border rounded-xl shadow-subtle space-y-1.5">
          <span className="text-[10px] font-mono text-text-muted uppercase">Precision</span>
          <div className="font-heading font-semibold text-2xl text-midnight font-mono tabular-nums">
            {(metrics.precision * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-text-secondary tabular-nums">
            {confusion_matrix.true_positives} / {confusion_matrix.true_positives + confusion_matrix.false_positives} predicted
          </span>
        </div>

        {/* F1-Score */}
        <div className="p-4 sm:p-4.5 bg-surface border border-border rounded-xl shadow-subtle space-y-1.5">
          <span className="text-[10px] font-mono text-text-muted uppercase">F1-Score</span>
          <div className="font-heading font-semibold text-2xl text-midnight font-mono tabular-nums">
            {metrics.f1_score.toFixed(4)}
          </div>
          <span className="text-[10px] text-text-secondary">Harmonic mean</span>
        </div>

        {/* ROC-AUC */}
        <div className="p-4 sm:p-4.5 bg-surface border border-border rounded-xl shadow-subtle space-y-1.5">
          <span className="text-[10px] font-mono text-text-muted uppercase">ROC-AUC</span>
          <div className="font-heading font-semibold text-2xl text-emerald-700 font-mono tabular-nums">
            {metrics.roc_auc.toFixed(4)}
          </div>
          <span className="text-[10px] text-text-secondary">Rank discrimination</span>
        </div>

        {/* Specificity */}
        <div className="p-4 sm:p-4.5 bg-surface border border-border rounded-xl shadow-subtle space-y-1.5">
          <span className="text-[10px] font-mono text-text-muted uppercase">Specificity</span>
          <div className="font-heading font-semibold text-2xl text-midnight font-mono tabular-nums">
            {(metrics.specificity * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-text-secondary tabular-nums">
            {confusion_matrix.true_negatives} / {confusion_matrix.true_negatives + confusion_matrix.false_positives} retained
          </span>
        </div>
      </div>

      {/* Row 2: Confusion Matrix & Class Distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6">
        {/* Confusion Matrix (2x2 Matrix Grid) */}
        <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-heading font-semibold text-sm text-midnight">
                Evaluation Confusion Matrix (N = {perfData.sample_size.toLocaleString()})
              </h3>
              <p className="text-xs text-text-secondary mt-1">
                Exact confusion matrix verified under locked decision boundary τ = 0.50
              </p>
            </div>
            <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-medium border border-slate-200">
              Holdout Cohort
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3.5 pt-1 font-mono">
            {/* True Negatives */}
            <div className="p-4 sm:p-4.5 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1.5">
              <div className="text-[10px] uppercase font-medium text-emerald-800 flex justify-between">
                <span>True Negatives (TN)</span>
                <span className="tabular-nums">
                  {((confusion_matrix.true_negatives / perfData.sample_size) * 100).toFixed(2)}%
                </span>
              </div>
              <div className="font-heading font-semibold text-2xl text-emerald-900 tabular-nums">
                {confusion_matrix.true_negatives}
              </div>
              <p className="text-[11px] text-emerald-700 font-sans leading-normal">
                Correctly identified retained accounts.
              </p>
            </div>

            {/* False Positives */}
            <div className="p-4 sm:p-4.5 rounded-xl bg-amber-50 border border-amber-200 space-y-1.5">
              <div className="text-[10px] uppercase font-medium text-amber-800 flex justify-between">
                <span>False Positives (FP)</span>
                <span className="tabular-nums">
                  {((confusion_matrix.false_positives / perfData.sample_size) * 100).toFixed(2)}%
                </span>
              </div>
              <div className="font-heading font-semibold text-2xl text-amber-900 tabular-nums">
                {confusion_matrix.false_positives}
              </div>
              <p className="text-[11px] text-amber-700 font-sans leading-normal">
                Retained customers falsely flagged at-risk (Type I error).
              </p>
            </div>

            {/* False Negatives */}
            <div className="p-4 sm:p-4.5 rounded-xl bg-rose-50 border border-rose-200 space-y-1.5">
              <div className="text-[10px] uppercase font-medium text-rose-800 flex justify-between">
                <span>False Negatives (FN)</span>
                <span className="tabular-nums">
                  {((confusion_matrix.false_negatives / perfData.sample_size) * 100).toFixed(2)}%
                </span>
              </div>
              <div className="font-heading font-semibold text-2xl text-rose-900 tabular-nums">
                {confusion_matrix.false_negatives}
              </div>
              <p className="text-[11px] text-rose-700 font-sans leading-normal">
                Churned customers missed by model (Type II error).
              </p>
            </div>

            {/* True Positives */}
            <div className="p-4 sm:p-4.5 rounded-xl bg-blue-50 border border-blue-200 space-y-1.5">
              <div className="text-[10px] uppercase font-medium text-blue-800 flex justify-between">
                <span>True Positives (TP)</span>
                <span className="tabular-nums">
                  {((confusion_matrix.true_positives / perfData.sample_size) * 100).toFixed(2)}%
                </span>
              </div>
              <div className="font-heading font-semibold text-2xl text-blue-950 tabular-nums">
                {confusion_matrix.true_positives}
              </div>
              <p className="text-[11px] text-blue-700 font-sans leading-normal">
                Successfully caught churn risk accounts.
              </p>
            </div>
          </div>
        </div>

        {/* Holdout Class Distribution Breakdown */}
        <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-5">
          <div>
            <h3 className="font-heading font-semibold text-sm text-midnight">
              Holdout Class Distribution & Calibration
            </h3>
            <p className="text-xs text-text-secondary mt-1">
              Actual vs Predicted class balance across the 1,500 evaluation instances
            </p>
          </div>

          <div className="space-y-4 pt-1">
            <div>
              <div className="flex justify-between text-xs font-mono mb-1.5">
                <span className="text-text-secondary">Actual Ground Truth (N = 1,500)</span>
                <span className="font-medium text-rose-700 tabular-nums">
                  {class_distributions.actual_churned} Churned ({(class_distributions.actual_churn_rate * 100).toFixed(2)}%)
                </span>
              </div>
              <div className="w-full h-2.5 rounded bg-slate-100 flex overflow-hidden">
                <div
                  className="bg-rose-500 h-full"
                  style={{ width: `${class_distributions.actual_churn_rate * 100}%` }}
                />
                <div
                  className="bg-emerald-600 h-full"
                  style={{ width: `${(1 - class_distributions.actual_churn_rate) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] font-mono text-text-muted mt-1.5 tabular-nums">
                <span>{class_distributions.actual_churned} Churned</span>
                <span>{class_distributions.actual_retained} Retained ({((class_distributions.actual_retained / 1500) * 100).toFixed(2)}%)</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono mb-1.5">
                <span className="text-text-secondary">Predicted (Decision Boundary τ = 0.50)</span>
                <span className="font-medium text-amber-700 tabular-nums">
                  {class_distributions.predicted_churned} At-Risk ({(class_distributions.predicted_churn_rate * 100).toFixed(2)}%)
                </span>
              </div>
              <div className="w-full h-2.5 rounded bg-slate-100 flex overflow-hidden">
                <div
                  className="bg-amber-500 h-full"
                  style={{ width: `${class_distributions.predicted_churn_rate * 100}%` }}
                />
                <div
                  className="bg-emerald-600 h-full"
                  style={{ width: `${(1 - class_distributions.predicted_churn_rate) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] font-mono text-text-muted mt-1.5 tabular-nums">
                <span>{class_distributions.predicted_churned} Predicted Churn</span>
                <span>{class_distributions.predicted_retained} Predicted Retained ({((class_distributions.predicted_retained / 1500) * 100).toFixed(2)}%)</span>
              </div>
            </div>

            <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-text-secondary space-y-1.5 font-mono">
              <div className="flex justify-between tabular-nums">
                <span>Average Precision (PR-AUC):</span>
                <strong className="text-midnight">{metrics.average_precision.toFixed(4)}</strong>
              </div>
              <div className="flex justify-between tabular-nums">
                <span>Brier Score (Mean Squared Prob Error):</span>
                <strong className="text-midnight">{metrics.brier_score.toFixed(4)}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Hyperparameter Spec & Disclosures */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6">
        {/* Hyperparameters Table */}
        <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-4">
          <div className="flex items-center gap-2 text-xs font-heading font-semibold text-midnight uppercase tracking-wider">
            <Cpu className="w-4 h-4 text-electric" /> Locked Hyperparameters (Config D)
          </div>
          <div className="border border-border rounded-xl overflow-hidden font-mono text-xs">
            <table className="w-full text-left">
              <thead className="bg-slate-50 text-text-muted uppercase text-[10px] border-b border-border">
                <tr>
                  <th className="py-2.5 px-3.5">Hyperparameter</th>
                  <th className="py-2.5 px-3.5 text-right">Configured Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {Object.entries(hyperparameters).map(([k, v]) => (
                  <tr key={k} className="hover:bg-slate-50/50">
                    <td className="py-2 px-3.5 text-text-secondary">{k}</td>
                    <td className="py-2 px-3.5 text-right font-medium text-midnight tabular-nums">{String(v)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Evaluation Disclosures */}
        <div className="p-6 sm:p-7 bg-surface border border-border rounded-xl shadow-subtle space-y-4">
          <div className="flex items-center gap-2 text-xs font-heading font-semibold text-midnight uppercase tracking-wider">
            <Info className="w-4 h-4 text-electric" /> Methodology & Calibration Disclosures
          </div>
          <div className="space-y-3.5 text-xs text-text-secondary leading-relaxed">
            <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <strong className="text-midnight block">Evaluation Methodology:</strong>
              <p>{perfData.methodology_disclosure}</p>
            </div>
            <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <strong className="text-midnight block">Calibration Notice:</strong>
              <p>{perfData.calibration_disclosure}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
