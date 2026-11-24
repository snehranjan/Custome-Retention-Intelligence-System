import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { Loader2 } from "lucide-react";

/**
 * RetainIQ Enterprise Design System - Button
 * Unslopped: 8px radius, quiet chrome, precision contrast, zero neon glows.
 */
export const Button = React.forwardRef(function Button(
  {
    children,
    variant = "primary",
    size = "md",
    className = "",
    disabled = false,
    loading = false,
    icon: Icon,
    iconPosition = "left",
    type = "button",
    ...props
  },
  ref
) {
  const baseStyles =
    "inline-flex items-center justify-center font-medium font-body transition-colors duration-150 select-none rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-electric focus-visible:ring-offset-2 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100";

  const variantStyles = {
    primary:
      "bg-electric text-white hover:bg-electric-dark shadow-subtle border border-transparent font-semibold",
    secondary:
      "bg-surface text-text-primary border border-border hover:bg-surface-muted hover:border-border-dark shadow-subtle",
    outline:
      "bg-transparent text-text-primary border border-border hover:bg-surface-muted hover:border-border-dark",
    ghost:
      "bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-muted",
    danger:
      "bg-danger text-white hover:bg-danger-dark shadow-subtle border border-transparent font-semibold",
    glow:
      "bg-midnight text-white border border-slate-700 hover:bg-midnight-50 shadow-subtle",
  };

  const sizeStyles = {
    sm: "text-xs px-2.5 py-1.5 gap-1.5 h-8",
    md: "text-xs sm:text-sm px-3.5 py-2 gap-2 h-9",
    lg: "text-sm sm:text-base px-5 py-2.5 gap-2.5 h-10 sm:h-11",
  };

  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      className={twMerge(clsx(baseStyles, variantStyles[variant], sizeStyles[size], className))}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin text-current" />
      ) : Icon && iconPosition === "left" ? (
        <Icon className="w-4 h-4 shrink-0 text-current" strokeWidth={1.75} />
      ) : null}
      <span>{children}</span>
      {!loading && Icon && iconPosition === "right" ? (
        <Icon className="w-4 h-4 shrink-0 text-current" strokeWidth={1.75} />
      ) : null}
    </button>
  );
});
