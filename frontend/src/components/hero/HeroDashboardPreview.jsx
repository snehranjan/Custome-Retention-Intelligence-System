import React from "react";
import { motion } from "framer-motion";
import {
  Users,
  TrendingDown,
  BarChart3,
  RefreshCw,
  Calendar,
  Sparkles,
} from "lucide-react";
import { HeroKpiCard } from "./HeroKpiCard";
import { ChurnRiskChart } from "./ChurnRiskChart";
import { CustomerRiskList } from "./CustomerRiskList";
import { PredictionPreview } from "./PredictionPreview";
import { Badge } from "../ui/Badge";
import { fadeUp, staggerContainer } from "../../utils/animations";

/**
 * RetainIQ Animated Product Dashboard Preview
 * Floating interactive analytics dashboard interface built with real React components, SVG, and CSS.
 * Explicitly labeled as an Illustrative Preview with sample demonstration data.
 */
export function HeroDashboardPreview() {
  return (
    <motion.div
      id="dashboard-preview"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="relative w-full max-w-2xl mx-auto lg:max-w-none"
    >
      {/* Main Elevated Dashboard Container - Unslopped (12px radius, quiet border, no outer glow) */}
      <div className="relative rounded-xl bg-surface border border-border shadow-card p-4 sm:p-5 overflow-hidden">
        {/* Dashboard Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3.5 mb-4 border-b border-border/70 gap-2.5">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono text-text-secondary bg-surface-muted border border-border">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>Interactive Preview</span>
            </span>

            <span className="px-2 py-0.5 text-[10.5px] font-mono text-text-muted rounded border border-border/60 bg-bg">
              Sample Cohort (N = 7,000)
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-[11px] font-mono text-text-muted">
            <Calendar className="w-3.5 h-3.5 text-text-muted shrink-0" />
            <span>Cutoff: 31 Dec 2025</span>
          </div>
        </div>

        {/* Dashboard Body Grid */}
        <div className="space-y-4">
          {/* Top 3 KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <HeroKpiCard
              icon={Users}
              label="Customers Analyzed"
              value="7,000"
              delta="100%"
              deltaType="positive"
              subtitle="Illustrative cohort dataset"
              iconColor="text-electric"
              iconBg="bg-electric/10"
            />
            <HeroKpiCard
              icon={TrendingDown}
              label="At-Risk Customers"
              value="1,840"
              delta="26.3%"
              deltaType="negative"
              subtitle="Risk Score ≥ 0.50"
              iconColor="text-danger"
              iconBg="bg-danger/10"
            />
            <HeroKpiCard
              icon={BarChart3}
              label="Avg Churn Risk"
              value="42.8%"
              delta="Threshold: 0.50"
              deltaType="neutral"
              subtitle="Across 5 customer segments"
              iconColor="text-warning"
              iconBg="bg-warning/10"
            />
          </div>

          {/* Middle Row: Churn Distribution & Prediction Preview */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-6">
              <ChurnRiskChart />
            </div>
            <div className="lg:col-span-6">
              <PredictionPreview />
            </div>
          </div>

          {/* Bottom Row: Customer Risk Explorer List */}
          <div>
            <CustomerRiskList />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
