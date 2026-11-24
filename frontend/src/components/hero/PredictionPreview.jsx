import React from "react";
import { Zap, ShieldAlert, Sparkles, ArrowRight } from "lucide-react";
import { Badge } from "../ui/Badge";

/**
 * RetainIQ Churn Risk Assessment Callout Panel
 * Realistic demonstration preview highlighting the illustrative risk score, friction factor, and intervention.
 */
export function PredictionPreview() {
  return (
    <div className="p-4 rounded-lg bg-surface border border-border shadow-subtle relative">
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-text-secondary" strokeWidth={1.75} />
          <span className="font-heading text-xs font-semibold text-midnight tracking-tight">
            Churn Risk Assessment
          </span>
        </div>
        <Badge variant="high_risk" dot={true} size="sm">
          High Risk
        </Badge>
      </div>

      <div className="mb-2.5">
        <div className="flex items-baseline gap-2 mb-1">
          <span className="font-heading text-2xl font-semibold text-danger tabular-nums">
            74.2%
          </span>
          <span className="text-xs text-text-secondary font-mono">
            Predicted Churn Score (τ = 0.50)
          </span>
        </div>
        <p className="text-xs text-text-secondary leading-relaxed">
          Primary friction factor: Delivery SLA latency (avg 4.8 days) combined with steep velocity decay.
        </p>
      </div>

      {/* Suggested Action Box */}
      <div className="p-2.5 rounded bg-surface-muted border border-border flex items-start gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-electric shrink-0 mt-1.5" />
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono font-medium uppercase text-text-secondary tracking-wide mb-0.5">
            Prescribed Intervention Strategy
          </div>
          <div className="text-xs text-text-primary leading-snug">
            Issue ₹150 apology credit and prioritize subsequent orders via Express Dispatch.
          </div>
        </div>
      </div>

      {/* Footnote */}
      <div className="mt-2.5 text-[10.5px] text-text-muted font-mono text-center">
        Illustrative diagnostic output based on 43 raw Config D features.
      </div>
    </div>
  );
}
