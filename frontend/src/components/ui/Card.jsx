import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * RetainIQ Enterprise Design System - Card
 * Unslopped: 12px radius, quiet hairline border, restrained subtle shadow, zero bouncy transforms.
 */
export function Card({
  children,
  variant = "surface",
  hover = false,
  className = "",
  as: Component = "div",
  ...props
}) {
  const variantStyles = {
    surface: "bg-surface border border-border shadow-card",
    elevated: "bg-surface border border-border shadow-elevated",
    subtle: "bg-bg-alt border border-border/70 shadow-subtle",
    recessed: "bg-surface-muted border border-border",
    midnight: "bg-midnight text-white border border-slate-800 shadow-elevated",
    glass: "bg-surface border border-border shadow-card", // Backwards-compatible alias without blur
  };

  const hoverStyle = hover
    ? "transition-colors duration-150 hover:border-border-dark"
    : "";

  return (
    <Component
      className={twMerge(
        clsx("rounded-xl p-5 sm:p-6", variantStyles[variant], hoverStyle, className)
      )}
      {...props}
    >
      {children}
    </Component>
  );
}
