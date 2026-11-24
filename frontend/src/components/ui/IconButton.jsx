import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * RetainIQ Enterprise Design System - Accessible Icon Button
 * Unslopped: nested 8px/6px radius, uniform 16px/18px icon scaling, quiet hover states.
 */
export const IconButton = React.forwardRef(function IconButton(
  {
    icon: Icon,
    label,
    variant = "ghost",
    size = "md",
    className = "",
    type = "button",
    disabled = false,
    ...props
  },
  ref
) {
  const baseStyles =
    "inline-flex items-center justify-center transition-colors duration-150 select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-electric focus-visible:ring-offset-2 active:scale-[0.97] disabled:opacity-50 disabled:pointer-events-none";

  const variantStyles = {
    primary: "bg-electric text-white hover:bg-electric-dark shadow-subtle border border-transparent",
    secondary: "bg-surface text-text-primary border border-border hover:bg-surface-muted hover:border-border-dark shadow-subtle",
    outline: "bg-transparent text-text-primary border border-border hover:bg-surface-muted hover:border-border-dark",
    ghost: "bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-muted",
    subtle: "bg-surface-muted text-text-secondary hover:text-text-primary hover:bg-border-light",
  };

  const sizeStyles = {
    sm: "w-8 h-8 rounded-md",
    md: "w-9 h-9 rounded-lg",
    lg: "w-10 h-10 rounded-lg",
  };

  const iconSizes = {
    sm: "w-4 h-4",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  return (
    <button
      ref={ref}
      type={type}
      aria-label={label}
      title={label}
      disabled={disabled}
      className={twMerge(clsx(baseStyles, variantStyles[variant], sizeStyles[size], className))}
      {...props}
    >
      <Icon className={iconSizes[size]} strokeWidth={1.75} aria-hidden="true" />
    </button>
  );
});
