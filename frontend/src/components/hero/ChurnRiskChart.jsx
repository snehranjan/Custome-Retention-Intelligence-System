import React, { useState } from "react";
import { motion } from "framer-motion";
import { PieChart, Info, ShieldAlert } from "lucide-react";

/**
 * RetainIQ Churn Risk Distribution Chart
 * Segmented visual breakdown displaying illustrative Low, Moderate, and High churn risk proportions.
 */
export function ChurnRiskChart() {
  const [activeTier, setActiveTier] = useState(null);

  const tiers = [
    {
      name: "Low Risk",
      range: "p < 0.50",
      percentage: 54.2,
      count: "3,794",
      color: "#16A34A",
      bgClass: "bg-emerald-500",
      borderClass: "border-emerald-300",
    },
    {
      name: "Moderate Risk",
      range: "0.50 ≤ p < 0.70",
      percentage: 19.5,
      count: "1,366",
      color: "#D97706",
      bgClass: "bg-amber-500",
      borderClass: "border-amber-300",
    },
    {
      name: "High Risk",
      range: "p ≥ 0.70",
      percentage: 26.3,
      count: "1,840",
      color: "#DC2626",
      bgClass: "bg-rose-500",
      borderClass: "border-rose-300",
    },
  ];

  return (
    <div className="p-4 rounded-lg bg-surface border border-border shadow-subtle">
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          <PieChart className="w-4 h-4 text-text-secondary" strokeWidth={1.75} />
          <h4 className="font-heading text-xs font-semibold text-midnight tracking-tight">
            Churn Risk Distribution
          </h4>
        </div>
        <span className="text-[11px] font-mono text-text-muted">
          Locked Threshold: τ = 0.50
        </span>
      </div>

      {/* Segmented Horizontal Distribution Bar (Clean 6px radius) */}
      <div className="h-2.5 w-full rounded-md bg-surface-muted flex overflow-hidden p-0.5 gap-0.5 mb-3 border border-border/60">
        {tiers.map((tier) => (
          <div
            key={tier.name}
            style={{ width: `${tier.percentage}%` }}
            onMouseEnter={() => setActiveTier(tier.name)}
            onMouseLeave={() => setActiveTier(null)}
            className={`h-full rounded-xs cursor-pointer transition-opacity ${tier.bgClass} ${
              activeTier && activeTier !== tier.name ? "opacity-40" : "opacity-100"
            }`}
            title={`${tier.name}: ${tier.percentage}% (${tier.count} customers)`}
          />
        ))}
      </div>

      {/* Legend & Breakdown Metrics */}
      <div className="grid grid-cols-3 gap-1 pt-2 border-t border-border/60">
        {tiers.map((tier) => (
          <div
            key={tier.name}
            onMouseEnter={() => setActiveTier(tier.name)}
            onMouseLeave={() => setActiveTier(null)}
            className={`p-1.5 rounded transition-colors cursor-default ${
              activeTier === tier.name ? "bg-surface-muted" : ""
            }`}
          >
            <div className="flex items-start gap-1.5 mb-0.5">
              <span className={`w-1.5 h-1.5 rounded-full ${tier.bgClass} shrink-0 mt-1`} />
              <div className="flex flex-col">
                <span className="text-[11px] font-medium text-text-primary leading-tight">
                  {tier.name}
                </span>
                <span className="text-[10px] font-mono text-text-muted">
                  {tier.range}
                </span>
              </div>
            </div>
            <div className="font-mono text-xs font-semibold text-midnight pl-3 tabular-nums">
              {tier.percentage}%
            </div>
            <div className="text-[10px] text-text-muted pl-3 font-mono">
              {tier.count} accounts
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
