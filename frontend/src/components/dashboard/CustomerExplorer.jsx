/**
 * RetainIQ Customer Retention Intelligence System
 * Module 2: Customer Explorer (Phase 8.4.8)
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Eye,
  BrainCircuit,
  Zap,
  Layers,
  MapPin,
  Calendar,
  DollarSign,
  Clock,
  Package,
  X,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { apiClient } from "../../lib/apiClient";

const SEGMENT_NAMES = {
  0: "Champions & High-Value Loyalists",
  1: "At-Risk / Lapsed Low-Value Customers",
  2: "Zero Delivered-Purchase Customers",
  3: "Steady Core Repeaters",
  4: "Recent Low-Ticket / New Promising Customers",
};

export function CustomerExplorer({ initialSegment = "ALL", onInspectPrediction }) {
  const [customers, setCustomers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pagination & Filtering state
  const [page, setPage] = useState(0);
  const [limit] = useState(20);
  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState(initialSegment);
  const [riskTier, setRiskTier] = useState("ALL");
  const [stateFilter, setStateFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("customer_id");
  const [sortDir, setSortDir] = useState("ASC");

  // Selected customer for Profile Drawer
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [livePredictionResult, setLivePredictionResult] = useState(null);

  // Handle Escape key to close customer profile drawer
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && selectedCustomer) {
        setSelectedCustomer(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedCustomer]);

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        limit,
        offset: page * limit,
        sort_by: sortBy,
        sort_dir: sortDir,
      };
      if (search.trim()) params.search = search.trim();
      if (segment !== "ALL") params.segment = segment;
      if (riskTier !== "ALL") params.risk_tier = riskTier;
      if (stateFilter !== "ALL") params.state = stateFilter;

      const res = await apiClient.customers.list(params);
      if (res?.success && res?.data) {
        setCustomers(res.data.items || []);
        setTotal(res.data.total || 0);
      } else {
        setError("Failed to fetch customer directory records.");
      }
    } catch (err) {
      setError(err.message || "Error contacting customer API.");
    } finally {
      setLoading(false);
    }
  }, [page, limit, search, segment, riskTier, stateFilter, sortBy, sortDir]);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  // Open Drawer and load customer detail with 43 features
  const openCustomerDetail = async (customerId) => {
    setDrawerLoading(true);
    setLivePredictionResult(null);
    try {
      const res = await apiClient.customers.getById(customerId);
      if (res?.success && res?.data) {
        setSelectedCustomer(res.data);
      }
    } catch (err) {
      alert("Error loading customer profile: " + err.message);
    } finally {
      setDrawerLoading(false);
    }
  };

  // Trigger live prediction from Drawer
  const runLiveInference = async (customerId) => {
    setPredicting(true);
    try {
      const res = await apiClient.customers.predict(customerId);
      if (res?.success && res?.data) {
        setLivePredictionResult(res.data);
      }
    } catch (err) {
      alert("Error during model inference: " + err.message);
    } finally {
      setPredicting(false);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6 sm:space-y-7">
      {/* Title & Filters Bar */}
      <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-4 sm:space-y-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div>
            <h2 className="font-heading text-lg font-semibold text-midnight">
              Customer Retention Explorer
            </h2>
            <p className="text-xs text-text-secondary mt-1">
              Authoritative directory of 7,000 customers with RFM segmentation, predictions, and behavioral attributes.
            </p>
          </div>
          <div className="text-xs font-mono text-text-muted">
            Found <strong className="text-midnight tabular-nums">{total.toLocaleString()}</strong> customers
          </div>
        </div>

        {/* Filters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-3.5 pt-1">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-text-muted absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search ID or name..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="w-full pl-9 pr-3.5 py-2.5 text-xs bg-bg border border-border rounded-lg focus:outline-none focus:border-electric focus:ring-1 focus:ring-electric/20 text-midnight placeholder:text-text-muted"
            />
          </div>

          {/* Segment Filter */}
          <div>
            <select
              value={segment}
              onChange={(e) => {
                setSegment(e.target.value);
                setPage(0);
              }}
              className="w-full px-3.5 py-2.5 text-xs bg-bg border border-border rounded-lg focus:outline-none focus:border-electric focus:ring-1 focus:ring-electric/20 text-text-primary"
            >
              <option value="ALL">All Segments (0–4)</option>
              <option value="0">Cluster 0: Champions</option>
              <option value="1">Cluster 1: At-Risk Lapsed</option>
              <option value="2">Cluster 2: Zero Delivered</option>
              <option value="3">Cluster 3: Steady Repeaters</option>
              <option value="4">Cluster 4: New Promising</option>
            </select>
          </div>

          {/* Risk Tier Filter */}
          <div>
            <select
              value={riskTier}
              onChange={(e) => {
                setRiskTier(e.target.value);
                setPage(0);
              }}
              className="w-full px-3.5 py-2.5 text-xs bg-bg border border-border rounded-lg focus:outline-none focus:border-electric focus:ring-1 focus:ring-electric/20 text-text-primary"
            >
              <option value="ALL">All Risk Tiers</option>
              <option value="LOW">Low Risk (&lt; 0.50)</option>
              <option value="MODERATE">Moderate Risk (0.50 – 0.70)</option>
              <option value="HIGH">High Risk (≥ 0.70)</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(0);
              }}
              className="w-full px-3.5 py-2.5 text-xs bg-bg border border-border rounded-lg focus:outline-none focus:border-electric focus:ring-1 focus:ring-electric/20 text-text-primary"
            >
              <option value="customer_id">Sort: Customer ID</option>
              <option value="churn_probability">Sort: Churn Probability</option>
              <option value="hist_delivered_order_value_inr">Sort: Spend (INR)</option>
              <option value="recency_delivered_days">Sort: Recency (Days)</option>
              <option value="hist_delivered_order_count">Sort: Order Count</option>
            </select>
          </div>

          {/* Sort Direction Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSortDir((d) => (d === "ASC" ? "DESC" : "ASC"));
                setPage(0);
              }}
              className="flex-1 px-3.5 py-2.5 text-xs font-mono font-medium rounded-lg bg-bg border border-border hover:bg-slate-50 flex items-center justify-center gap-1.5 text-midnight transition shadow-subtle"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-electric" />
              <span>{sortDir}</span>
            </button>
            <button
              onClick={() => {
                setSearch("");
                setSegment("ALL");
                setRiskTier("ALL");
                setStateFilter("ALL");
                setSortBy("customer_id");
                setSortDir("ASC");
                setPage(0);
              }}
              className="p-2.5 rounded-lg border border-border hover:bg-slate-50 text-text-secondary text-xs transition shadow-subtle"
              title="Reset Filters"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-surface border border-border rounded-xl shadow-subtle overflow-hidden">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center text-text-secondary">
            <Loader2 className="w-6 h-6 animate-spin text-electric mb-2" />
            <p className="text-xs font-mono text-text-muted">Loading customers...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 font-mono">
            {error}
          </div>
        ) : customers.length === 0 ? (
          <div className="py-16 text-center text-text-muted space-y-2">
            <Search className="w-8 h-8 mx-auto opacity-40" />
            <p className="text-xs font-mono">No customers found matching the selected filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border bg-slate-50/75 text-text-muted font-mono uppercase text-[10px]">
                  <th className="py-3 px-4.5">Customer</th>
                  <th className="py-3 px-4.5">Location</th>
                  <th className="py-3 px-4.5">Persona Segment</th>
                  <th className="py-3 px-4.5 text-center">Risk Tier</th>
                  <th className="py-3 px-4.5 text-right">Probability</th>
                  <th className="py-3 px-4.5 text-right">Orders / Spend</th>
                  <th className="py-3 px-4.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {customers.map((c) => {
                  const prob = c.churn_probability !== null ? (c.churn_probability * 100).toFixed(1) : "—";
                  const tier = c.risk_tier || "UNKNOWN";
                  const tierColor =
                    tier === "HIGH"
                      ? "text-rose-700 bg-rose-50 border-rose-200"
                      : tier === "MODERATE"
                      ? "text-amber-700 bg-amber-50 border-amber-200"
                      : "text-emerald-700 bg-emerald-50 border-emerald-200";

                  return (
                    <tr
                      key={c.customer_id}
                      onClick={() => openCustomerDetail(c.customer_id)}
                      className="hover:bg-slate-50/60 cursor-pointer transition"
                    >
                      <td className="py-3.5 px-4.5">
                        <div className="font-medium text-midnight">{c.customer_name}</div>
                        <div className="text-[11px] font-mono text-text-muted">{c.customer_id}</div>
                      </td>
                      <td className="py-3.5 px-4.5 text-text-secondary">
                        <div>{c.city || "—"}</div>
                        <div className="text-[10px] text-text-muted">{c.state || "—"}</div>
                      </td>
                      <td className="py-3.5 px-4.5">
                        <span className="font-medium text-midnight block">
                          {c.segment_name || "Unassigned"}
                        </span>
                        <span className="text-[10px] font-mono text-text-muted">
                          Cluster {c.cluster_id ?? "—"}
                        </span>
                      </td>
                      <td className="py-3.5 px-4.5 text-center">
                        <span className={`inline-block px-2.5 py-0.5 rounded text-[10px] font-mono font-medium border ${tierColor}`}>
                          {tier}
                        </span>
                      </td>
                      <td className="py-3.5 px-4.5 text-right font-mono font-medium tabular-nums">
                        <span className={c.churn_probability >= 0.5 ? "text-rose-700" : "text-emerald-700"}>
                          {prob}%
                        </span>
                        <div className="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden ml-auto mt-1.5">
                          <div
                            className={c.churn_probability >= 0.5 ? "bg-rose-500 h-full" : "bg-emerald-600 h-full"}
                            style={{ width: `${Math.min(100, Math.max(0, (c.churn_probability || 0) * 100))}%` }}
                          />
                        </div>
                      </td>
                      <td className="py-3.5 px-4.5 text-right font-mono tabular-nums">
                        <div className="font-medium text-midnight">
                          ₹{(c.hist_delivered_order_value_inr || 0).toLocaleString()}
                        </div>
                        <div className="text-[10px] text-text-muted">
                          {c.hist_delivered_order_count || 0} orders • {c.recency_delivered_days ? `${Math.round(c.recency_delivered_days)}d ago` : "No delivered orders"}
                        </div>
                      </td>
                      <td className="py-3.5 px-4.5 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => openCustomerDetail(c.customer_id)}
                            className="px-3 py-1.5 rounded-lg border border-border hover:bg-slate-50 text-text-secondary hover:text-midnight text-[11px] font-medium flex items-center gap-1.5 transition shadow-subtle"
                          >
                            <Eye className="w-3.5 h-3.5 text-electric" />
                            <span>View</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="p-4 sm:p-4.5 border-t border-border bg-slate-50/50 flex items-center justify-between text-xs font-mono text-text-secondary">
          <div>
            Showing <strong className="text-midnight tabular-nums">{customers.length > 0 ? page * limit + 1 : 0}</strong> to{" "}
            <strong className="text-midnight tabular-nums">{Math.min((page + 1) * limit, total)}</strong> of{" "}
            <strong className="text-midnight tabular-nums">{total.toLocaleString()}</strong>
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="p-2 rounded-lg border border-border bg-surface hover:bg-slate-50 disabled:opacity-30 disabled:pointer-events-none text-text-secondary transition shadow-subtle"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page {page + 1} of {Math.max(1, totalPages)}
            </span>
            <button
              disabled={page + 1 >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="p-2 rounded-lg border border-border bg-surface hover:bg-slate-50 disabled:opacity-30 disabled:pointer-events-none text-text-secondary transition shadow-subtle"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Customer Profile Drawer Modal */}
      {selectedCustomer && (
        <div 
          className="fixed inset-0 z-50 bg-midnight/40 backdrop-blur-sm flex justify-end cursor-pointer"
          onClick={() => setSelectedCustomer(null)}
        >
          <div 
            className="w-full max-w-2xl bg-surface border-l border-border h-full overflow-y-auto p-6 sm:p-7 space-y-6 sm:space-y-7 shadow-2xl animate-in slide-in-from-right duration-200 cursor-default"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div className="flex items-start justify-between pb-5 border-b border-border">
              <div>
                <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-medium uppercase border border-slate-200">
                  Customer Profile
                </span>
                <h3 className="font-heading font-semibold text-lg text-midnight mt-1.5">
                  {selectedCustomer.customer_name}
                </h3>
                <p className="text-xs font-mono text-text-muted mt-1">
                  ID: {selectedCustomer.customer_id} • Signed up: {selectedCustomer.signup_date}
                </p>
              </div>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="p-2 rounded-lg border border-border hover:bg-slate-50 text-text-secondary transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Intelligence Summary Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
              {/* Persona Segment */}
              <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <span className="text-[10px] text-text-muted font-mono uppercase">Persona Segment</span>
                <div className="font-medium text-xs text-midnight">
                  {selectedCustomer.current_segment?.segment_name || "Unassigned"}
                </div>
                <div className="text-[10px] font-mono text-electric pt-0.5">
                  Cluster {selectedCustomer.current_segment?.cluster_id ?? "—"}
                </div>
              </div>

              {/* Churn Probability */}
              <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <span className="text-[10px] text-text-muted font-mono uppercase">Churn Risk Score</span>
                <div className="font-mono font-medium text-base tabular-nums">
                  <span className={(selectedCustomer.latest_prediction?.churn_probability ?? 0) >= 0.5 ? "text-rose-700" : "text-emerald-700"}>
                    {selectedCustomer.latest_prediction?.churn_probability !== undefined
                      ? `${(selectedCustomer.latest_prediction.churn_probability * 100).toFixed(1)}%`
                      : "—"}
                  </span>
                </div>
                <div className="text-[10px] font-mono text-text-secondary pt-0.5">
                  Tier: <strong>{selectedCustomer.latest_prediction?.risk_tier || "—"}</strong>
                </div>
              </div>

              {/* Ground Truth Outcome */}
              <div className="p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <span className="text-[10px] text-text-muted font-mono uppercase">Observed Outcome</span>
                <div className="font-medium text-xs flex items-center gap-1.5">
                  {selectedCustomer.churn === 1 ? (
                    <>
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                      <span className="text-rose-700">Observed Churned</span>
                    </>
                  ) : (
                    <>
                      <span className="w-2 h-2 rounded-full bg-emerald-600" />
                      <span className="text-emerald-700">Observed Retained</span>
                    </>
                  )}
                </div>
                <div className="text-[10px] font-mono text-text-muted pt-0.5">
                  Window: Q1 2026
                </div>
              </div>
            </div>

            {/* Live Model Re-Inference Box */}
            <div className="p-5 sm:p-6 rounded-xl bg-slate-50 border border-border space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4 text-electric" />
                  <span className="text-xs font-heading font-semibold text-midnight">
                    Live Random Forest Inference (τ = 0.50)
                  </span>
                </div>
                <button
                  disabled={predicting}
                  onClick={() => runLiveInference(selectedCustomer.customer_id)}
                  className="px-3.5 py-2 text-xs font-medium rounded-lg bg-electric text-white hover:bg-electric-hover disabled:opacity-50 transition flex items-center gap-1.5 shadow-subtle"
                >
                  {predicting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <BrainCircuit className="w-3.5 h-3.5" />}
                  <span>{predicting ? "Evaluating..." : "Run Live Inference"}</span>
                </button>
              </div>

              {livePredictionResult && (
                <div className="p-4 rounded-xl bg-surface border border-slate-200 space-y-2.5 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-secondary">Evaluated Probability:</span>
                    <span className="font-mono font-medium text-sm text-midnight tabular-nums">
                      {(livePredictionResult.churn_probability * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-secondary">Class Label:</span>
                    <span className={`font-mono font-medium px-2.5 py-0.5 rounded text-[10px] ${
                      livePredictionResult.predicted_class === 1 ? "bg-rose-50 text-rose-700 border border-rose-200" : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    }`}>
                      {livePredictionResult.predicted_class === 1 ? "CHURN (1)" : "RETAINED (0)"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-secondary">Risk Tier:</span>
                    <span className="font-mono font-medium text-midnight">
                      {livePredictionResult.risk_tier}
                    </span>
                  </div>
                  <p className="text-[10px] font-mono text-text-muted pt-1">
                    Verified via locked production pipeline SHA-256 (24F1F0E3...3438F301).
                  </p>
                </div>
              )}
            </div>

            {/* Prescriptive Recommendations for this customer */}
            <div className="space-y-3.5">
              <h4 className="text-xs font-heading font-semibold text-midnight uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-electric" /> Prescriptive Retention Actions ({selectedCustomer.recommendations?.length || 0})
              </h4>
              {selectedCustomer.recommendations?.length > 0 ? (
                <div className="space-y-3">
                  {selectedCustomer.recommendations.map((rec, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-midnight">{rec.recommendation_title}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${
                          rec.priority === "HIGH" ? "bg-rose-50 text-rose-700 border-rose-200" : "bg-amber-50 text-amber-700 border-amber-200"
                        }`}>
                          {rec.priority}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary leading-relaxed">
                        {rec.recommendation_description}
                      </p>
                      <div className="text-[11px] font-mono text-text-muted flex justify-between pt-1.5 border-t border-slate-200/60">
                        <span>Category: <strong>{rec.recommendation_category}</strong></span>
                        <span>Status: <strong>{rec.recommendation_status}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-muted font-mono p-4 bg-slate-50 rounded-xl border border-slate-200">
                  No active retention actions triggered for this account.
                </p>
              )}
            </div>

            {/* 43 Behavioral Features Breakdown */}
            <div className="space-y-3.5">
              <h4 className="text-xs font-heading font-semibold text-midnight uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-electric" /> Authoritative 43 Behavioral Features
              </h4>
              {selectedCustomer.features ? (
                <div className="max-h-60 overflow-y-auto border border-border rounded-xl">
                  <table className="w-full text-left text-[11px]">
                    <thead className="sticky top-0 bg-slate-50 text-text-muted font-mono uppercase text-[10px] border-b border-border">
                      <tr>
                        <th className="py-2.5 px-3.5">Feature Name</th>
                        <th className="py-2.5 px-3.5 text-right">Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border font-mono">
                      {Object.entries(selectedCustomer.features).map(([key, val]) => (
                        <tr key={key} className="hover:bg-slate-50/50">
                          <td className="py-2 px-3.5 text-text-secondary">{key}</td>
                          <td className="py-2 px-3.5 text-right font-medium text-midnight tabular-nums">
                            {val === null ? <span className="text-text-muted font-normal">null</span> : String(val)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-text-muted font-mono">Features table loading...</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
