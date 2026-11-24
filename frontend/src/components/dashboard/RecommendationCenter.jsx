/**
 * RetainIQ Customer Retention Intelligence System
 * Module 5: Retention Recommendation Center (Phase 8.4.8)
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Zap,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Send,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Eye,
  Loader2,
  RefreshCw,
  MessageSquare,
  Mail,
  UserCheck,
  Bell,
  ArrowUpRight,
} from "lucide-react";
import { apiClient } from "../../lib/apiClient";

export function RecommendationCenter({ onSelectCustomer }) {
  const [recommendations, setRecommendations] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter state
  const [page, setPage] = useState(0);
  const [limit] = useState(15);
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("ALL");
  const [segment, setSegment] = useState("ALL");
  const [riskTier, setRiskTier] = useState("ALL");

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        limit,
        offset: page * limit,
      };
      if (search.trim()) params.search = search.trim();
      if (priority !== "ALL") params.priority = priority;
      if (segment !== "ALL") params.segment = segment;
      if (riskTier !== "ALL") params.risk_tier = riskTier;

      const res = await apiClient.recommendations.list(params);
      if (res?.success && res?.data) {
        setRecommendations(res.data.items || []);
        setTotal(res.data.total || 0);
      } else {
        setError("Failed to fetch retention recommendations.");
      }
    } catch (err) {
      setError(err.message || "Error contacting recommendations API.");
    } finally {
      setLoading(false);
    }
  }, [page, limit, search, priority, segment, riskTier]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const totalPages = Math.ceil(total / limit);

  const getChannelIcon = (channel) => {
    if (!channel) return <Bell className="w-3.5 h-3.5" />;
    if (channel.includes("Concierge") || channel.includes("Account")) return <UserCheck className="w-3.5 h-3.5 text-electric" />;
    if (channel.includes("SMS") || channel.includes("WhatsApp")) return <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />;
    if (channel.includes("Email")) return <Mail className="w-3.5 h-3.5 text-cyan" />;
    return <Bell className="w-3.5 h-3.5 text-amber-500" />;
  };

  return (
    <div className="space-y-5 sm:space-y-6">
      {/* Title & Filter Header */}
      <div className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle space-y-4 sm:space-y-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 sm:gap-4">
          <div>
            <h2 className="font-heading text-lg sm:text-xl font-semibold text-midnight flex items-center gap-2.5">
              <Zap className="w-5 h-5 text-electric shrink-0" />
              <span>Prescriptive Retention Recommendations</span>
            </h2>
            <p className="text-xs sm:text-[13px] text-text-secondary mt-1.5 leading-relaxed">
              16,580 rule-based intervention playbooks tailored to customer risk tiers and RFM segments.
            </p>
          </div>
          <div className="text-xs font-mono text-text-muted bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200 shrink-0">
            Found <strong className="text-midnight tabular-nums">{total.toLocaleString()}</strong> actions
          </div>
        </div>

        {/* Filter Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 pt-1">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-text-muted absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search customer, action, or ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="w-full pl-10 pr-3.5 py-2.5 text-xs bg-bg border border-border rounded-lg focus:outline-none focus:border-electric focus:ring-1 focus:ring-electric/20 font-mono text-midnight placeholder:text-text-muted"
            />
          </div>

          {/* Priority */}
          <div>
            <select
              value={priority}
              onChange={(e) => {
                setPriority(e.target.value);
                setPage(0);
              }}
              className="w-full px-3.5 py-2.5 text-xs bg-bg border border-border rounded-lg focus:outline-none focus:border-electric focus:ring-1 focus:ring-electric/20 text-text-primary"
            >
              <option value="ALL">All Priorities</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          {/* Segment */}
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

          {/* Reset button */}
          <div className="flex items-center">
            <button
              onClick={() => {
                setSearch("");
                setPriority("ALL");
                setSegment("ALL");
                setRiskTier("ALL");
                setPage(0);
              }}
              className="w-full px-4 py-2.5 text-xs font-medium rounded-lg bg-bg border border-border hover:bg-slate-50 text-midnight flex items-center justify-center gap-2 transition shadow-subtle"
            >
              <RefreshCw className="w-3.5 h-3.5 text-electric" />
              <span>Reset Filters</span>
            </button>
          </div>
        </div>
      </div>

      {/* Cards List */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-text-secondary bg-surface border border-border rounded-xl shadow-subtle">
          <Loader2 className="w-6 h-6 animate-spin text-electric mb-2" />
          <p className="text-xs font-mono text-text-muted">Loading recommendations...</p>
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 font-mono bg-surface border border-border rounded-xl shadow-subtle">
          {error}
        </div>
      ) : recommendations.length === 0 ? (
        <div className="py-16 text-center text-text-muted space-y-2 bg-surface border border-border rounded-xl shadow-subtle">
          <Zap className="w-8 h-8 mx-auto opacity-40" />
          <p className="text-xs font-mono">No retention recommendations match the selected filters.</p>
        </div>
      ) : (
        <div className="space-y-4 sm:space-y-5">
          {recommendations.map((rec) => {
            const prob = rec.churn_probability !== null ? (rec.churn_probability * 100).toFixed(1) : "—";
            const priorityBadge =
              rec.priority === "HIGH"
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : rec.priority === "MEDIUM"
                ? "bg-amber-50 text-amber-700 border-amber-200"
                : "bg-emerald-50 text-emerald-700 border-emerald-200";

            return (
              <div
                key={rec.recommendation_id}
                className="p-5 sm:p-6 bg-surface border border-border rounded-xl shadow-subtle hover:border-slate-300 transition space-y-4 sm:space-y-4.5"
              >
                {/* Header: Action Title, Priority, Channel */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-0.5">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className={`px-2.5 py-1 rounded-md text-[10px] font-mono font-medium border ${priorityBadge}`}>
                      {rec.priority} PRIORITY
                    </span>
                    <span className="text-xs font-mono text-text-muted px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200">
                      {rec.category}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-xs font-mono text-midnight bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200">
                    {getChannelIcon(rec.suggested_channel)}
                    <span>Channel: <strong>{rec.suggested_channel}</strong></span>
                  </div>
                </div>

                {/* Body: Action Title & Description */}
                <div className="space-y-1.5">
                  <h3 className="font-heading font-semibold text-base sm:text-lg text-midnight">
                    {rec.suggested_action}
                  </h3>
                  <p className="text-xs sm:text-[13px] text-text-secondary leading-relaxed">
                    {rec.reason}
                  </p>
                </div>

                {/* Evidence Strip */}
                {rec.evidence && (
                  <div className="p-3.5 sm:p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 font-mono flex items-start gap-3 my-1">
                    <span className="text-electric font-semibold shrink-0">Evidence:</span>
                    <span className="leading-relaxed">{rec.evidence}</span>
                  </div>
                )}

                {/* Footer: Linked Customer & View Action */}
                <div className="pt-4 sm:pt-4.5 mt-1 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3.5 sm:gap-4 border-t border-border text-xs">
                  <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-text-secondary font-mono text-[11.5px]">
                    <div>
                      Customer: <strong className="text-midnight">{rec.customer_name || rec.customer_id}</strong>
                    </div>
                    <div>
                      Segment: <strong className="text-midnight">{rec.segment_name}</strong>
                    </div>
                    <div className="tabular-nums">
                      Risk: <strong className={rec.churn_probability >= 0.5 ? "text-rose-700" : "text-emerald-700"}>{prob}%</strong>
                    </div>
                  </div>

                  <button
                    onClick={() => onSelectCustomer(rec.customer_id)}
                    className="px-4 py-2 text-xs font-medium rounded-lg bg-electric text-white hover:bg-electric-hover transition flex items-center gap-2 self-end sm:self-auto shadow-subtle"
                  >
                    <span>Inspect Profile</span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-blue-200" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      <div className="p-4 sm:p-4.5 border border-border rounded-xl bg-surface flex items-center justify-between text-xs font-mono text-text-secondary shadow-subtle mt-6 sm:mt-7">
        <div className="tabular-nums">
          Page {page + 1} of {Math.max(1, totalPages)} ({total.toLocaleString()} total actions)
        </div>
        <div className="flex items-center gap-2">
          <button
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            className="p-2 rounded-md border border-border bg-surface hover:bg-slate-50 disabled:opacity-30 disabled:pointer-events-none transition shadow-subtle"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            disabled={page + 1 >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="p-2 rounded-md border border-border bg-surface hover:bg-slate-50 disabled:opacity-30 disabled:pointer-events-none transition shadow-subtle"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
