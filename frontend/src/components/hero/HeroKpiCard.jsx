import React from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { cardHover } from "../../utils/animations";

/**
 * RetainIQ Hero KPI Card
 * Illustrative demonstration metric card with icon, value, delta, and subtitle.
 */
export function HeroKpiCard({
  icon: Icon,
  label,
  value,
  delta,
  deltaType = "positive",
  subtitle,
}) {
  return (
    <div className="p-3.5 rounded-lg bg-surface border border-border shadow-subtle flex flex-col justify-between">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-text-secondary truncate">
          {label}
        </span>
        <Icon className="w-4 h-4 text-text-muted shrink-0" strokeWidth={1.75} />
      </div>

      <div className="flex flex-wrap items-baseline gap-2 mb-0.5">
        <span className="font-heading text-xl sm:text-2xl font-semibold text-midnight tracking-tight tabular-nums">
          {value}
        </span>
        {delta && (
          <span
            className={`inline-flex items-center text-[10px] font-mono px-1.5 py-0.5 rounded ${
              deltaType === "positive"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : deltaType === "negative"
                ? "bg-rose-50 text-rose-800 border border-rose-200"
                : "bg-amber-50 text-amber-800 border border-amber-200"
            }`}
          >
            <span>{delta}</span>
          </span>
        )}
      </div>

      {subtitle && (
        <span className="text-[11px] text-text-muted leading-tight block">
          {subtitle}
        </span>
      )}
    </div>
  );
}
