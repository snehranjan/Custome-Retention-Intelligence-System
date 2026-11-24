import React from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

/**
 * RetainIQ Enterprise Theme Toggle Component
 * Provides an accessible, keyboard-interactive, compact light/dark mode switch.
 *
 * Requirements:
 * - Lucide Sun icon for Light Mode, Moon icon for Dark Mode.
 * - Clear active theme indication and smooth restrained transition.
 * - Accessible ARIA attributes: role="switch", aria-checked, aria-label.
 * - Visible focus indicators and hover states.
 * - Works consistently across desktop, tablet, and mobile navigation headers.
 */
export function ThemeToggle({
  className = "",
  size = "md",
  showLabel = false,
  variant = "button", // 'button' | 'pill'
}) {
  const { theme, toggleTheme, isDark } = useTheme();

  const sizeClasses = {
    sm: "w-8 h-8 text-xs",
    md: "w-9 h-9 text-sm",
    lg: "w-10 h-10 text-base",
  };

  const iconSizes = {
    sm: "w-4 h-4",
    md: "w-4.5 h-4.5",
    lg: "w-5 h-5",
  };

  if (variant === "pill") {
    return (
      <button
        type="button"
        role="switch"
        aria-checked={isDark}
        aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
        title={isDark ? "Switch to light theme" : "Switch to dark theme"}
        onClick={toggleTheme}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-border bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-electric focus-visible:ring-offset-2 focus-visible:ring-offset-surface ${className}`}
      >
        {isDark ? (
          <>
            <Moon className="w-4 h-4 text-electric shrink-0" strokeWidth={1.75} />
            <span className="text-xs font-medium font-body">Dark</span>
          </>
        ) : (
          <>
            <Sun className="w-4 h-4 text-amber-500 shrink-0" strokeWidth={1.75} />
            <span className="text-xs font-medium font-body">Light</span>
          </>
        )}
      </button>
    );
  }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
      onClick={toggleTheme}
      className={`inline-flex items-center justify-center rounded-lg border border-border bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors duration-150 select-none shadow-subtle focus:outline-none focus-visible:ring-2 focus-visible:ring-electric focus-visible:ring-offset-2 focus-visible:ring-offset-surface active:scale-[0.97] ${sizeClasses[size] || sizeClasses.md} ${className}`}
    >
      {isDark ? (
        <Sun
          className={`${iconSizes[size] || iconSizes.md} text-amber-400 shrink-0 transition-transform duration-200 hover:rotate-12`}
          strokeWidth={1.85}
          aria-hidden="true"
        />
      ) : (
        <Moon
          className={`${iconSizes[size] || iconSizes.md} text-text-secondary shrink-0 transition-transform duration-200 hover:-rotate-12`}
          strokeWidth={1.85}
          aria-hidden="true"
        />
      )}
      {showLabel && (
        <span className="ml-2 text-xs font-medium font-body">
          {isDark ? "Light" : "Dark"}
        </span>
      )}
    </button>
  );
}
