import React from "react";
import { Users, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { Badge } from "../ui/Badge";

/**
 * RetainIQ Illustrative Customer Risk List
 * Renders sample customer accounts with official RFM persona tags and illustrative churn risk status.
 */
export function CustomerRiskList() {
  const sampleCustomers = [
    {
      id: "IND_CUST_1024",
      segment: "Champions & High-Value Loyalists",
      clusterId: 0,
      riskLevel: "Low",
      riskScore: "14%",
      variant: "success",
      segmentColor: "bg-purple-50 text-purple-700 border-purple-200",
      city: "Bengaluru",
    },
    {
      id: "IND_CUST_2087",
      segment: "Steady Core Repeaters",
      clusterId: 3,
      riskLevel: "Moderate",
      riskScore: "46%",
      variant: "warning",
      segmentColor: "bg-blue-50 text-blue-700 border-blue-200",
      city: "Mumbai",
    },
    {
      id: "IND_CUST_3156",
      segment: "At-Risk / Lapsed Low-Value Customers",
      clusterId: 1,
      riskLevel: "High",
      riskScore: "78%",
      variant: "danger",
      segmentColor: "bg-amber-50 text-amber-700 border-amber-200",
      city: "Delhi",
    },
  ];

  return (
    <div className="p-4 sm:p-5 rounded-xl bg-surface border border-border shadow-subtle">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-electric" />
          <h4 className="font-heading text-xs sm:text-sm font-bold text-midnight tracking-tight">
            Customer Risk Explorer
          </h4>
        </div>
        <span className="text-[10px] uppercase font-heading font-semibold text-text-muted tracking-wider">
          Sample Cohort
        </span>
      </div>

      {/* Responsive Customer Row List */}
      <div className="space-y-2">
        {sampleCustomers.map((cust) => (
          <div
            key={cust.id}
            className="p-2.5 rounded-lg border border-border/80 bg-bg hover:bg-surface hover:border-electric/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-3 text-xs"
          >
            {/* Customer ID & City */}
            <div className="flex items-center justify-between sm:justify-start sm:flex-col sm:items-start min-w-[110px] shrink-0">
              <span className="font-heading font-bold text-midnight truncate">
                {cust.id}
              </span>
              <span className="text-[10px] text-text-muted">
                {cust.city}, India
              </span>
            </div>

            {/* Persona Badge (Visible across viewports, wraps smoothly) */}
            <div className="flex-1 min-w-0">
              <span
                className={`inline-block px-2 py-0.5 text-[10px] font-heading font-medium rounded-md border leading-tight ${cust.segmentColor}`}
                title={cust.segment}
              >
                {cust.segment}
              </span>
            </div>

            {/* Risk Tier Badge & Score */}
            <div className="flex items-center justify-end gap-2 shrink-0 self-end sm:self-center">
              <Badge variant={cust.variant} dot={true} size="sm">
                {cust.riskLevel}
              </Badge>
              <span className="font-heading font-bold text-midnight text-[11px] w-8 text-right">
                {cust.riskScore}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
