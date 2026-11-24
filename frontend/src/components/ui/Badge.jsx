import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * RetainIQ Enterprise Design System - Semantic Status Badge
 * Unslopped: 6px radius (rounded-md), operational risk tiers (LOW/MODERATE/HIGH),
 * distinct employee status styles (APPROVED/PENDING/INVITED/REJECTED/SUSPENDED),
 * and accessible high-contrast color roles.
 */
export function Badge({
  children,
  variant = "primary",
  dot = false,
  size = "md",
  className = "",
  ...props
}) {
  const variantStyles = {
    // Brand & General
    primary: "bg-blue-50 text-blue-700 border-blue-200",
    secondary: "bg-slate-100 text-slate-700 border-slate-200",
    neutral: "bg-slate-100 text-slate-600 border-slate-200",
    midnight: "bg-midnight text-slate-200 border-slate-700",

    // Semantic Risk Tiers (Mandatory 3 tiers)
    low_risk: "bg-emerald-50 text-emerald-800 border-emerald-200",
    moderate_risk: "bg-amber-50 text-amber-800 border-amber-200",
    high_risk: "bg-rose-50 text-rose-800 border-rose-200",

    // Semantic System Status Aliases
    success: "bg-emerald-50 text-emerald-800 border-emerald-200",
    warning: "bg-amber-50 text-amber-800 border-amber-200",
    danger: "bg-rose-50 text-rose-800 border-rose-200",
    info: "bg-sky-50 text-sky-800 border-sky-200",

    // Employee Registry Statuses (Textual + Visual)
    approved: "bg-emerald-50 text-emerald-800 border-emerald-200",
    pending: "bg-amber-50 text-amber-800 border-amber-200",
    invited: "bg-sky-50 text-sky-800 border-sky-200",
    rejected: "bg-rose-50 text-rose-800 border-rose-200",
    suspended: "bg-slate-100 text-slate-700 border-slate-300",
  };

  const dotColorStyles = {
    primary: "bg-blue-600",
    secondary: "bg-slate-600",
    neutral: "bg-slate-500",
    midnight: "bg-sky-400",
    low_risk: "bg-emerald-600",
    moderate_risk: "bg-amber-600",
    high_risk: "bg-rose-600",
    success: "bg-emerald-600",
    warning: "bg-amber-600",
    danger: "bg-rose-600",
    info: "bg-sky-600",
    approved: "bg-emerald-600",
    pending: "bg-amber-600",
    invited: "bg-sky-600",
    rejected: "bg-rose-600",
    suspended: "bg-slate-500",
  };

  const sizeStyles = {
    sm: "text-[11px] font-medium px-2 py-0.5 gap-1.5",
    md: "text-xs font-medium px-2.5 py-0.5 gap-1.5",
    lg: "text-xs font-semibold px-3 py-1 gap-2",
  };

  return (
    <span
      className={twMerge(
        clsx(
          "inline-flex items-center rounded-md border select-none",
          variantStyles[variant] || variantStyles.neutral,
          sizeStyles[size],
          className
        )
      )}
      {...props}
    >
      {dot && (
        <span
          className={clsx("w-1.5 h-1.5 rounded-full shrink-0", dotColorStyles[variant] || "bg-current")}
          aria-hidden="true"
        />
      )}
      <span>{children}</span>
    </span>
  );
}
